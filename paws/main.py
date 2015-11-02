from __future__ import print_function
from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser
from util import zipdir
from config import get_config


def get_path_segments(path):
    """splits a path into its segments

    Args:
        path (str): the path to explode

    Returns:
        list(str): list of path segments, in order
    """
    parts = filter(None, path.split("/"))
    return parts


def get_resource_by_path(path, resources):
    """gets the resource that matches given path

    Args:
        path (str): path to find
        resources (list(str)): list of resources

    Returns:
        dict: resource that matches given path, None otherwise
    """
    return next(
        (x for x in resources if x['path'] == path),
        None)


def create_resource_path(api_connection, api_id, path, resources):
    """creates all resources necessary for a path

    Args:
        api_connection (ApiGatewayConnection): api gateway client
        api_id (str): id of the api to operate on
        path (str): path to create

    Returns:
        str: id of the resource that was created
    """

    segments = get_path_segments(path)
    parent_id = get_resource_by_path("/", resources)['id']

    for segment in segments:

        response = api_connection.create_resource(
            api_id, parent_id, segment)
        resources.append(response)

        parent_id = response["id"]

    return parent_id, resources


def get_resources_to_delete(resources):
    """returns a list of all resource ids to delete

    Args:
        resources (list(dict)): resources to compare to the paths

    Returns:
        list(str): list of ids of resources to remove
    """
    resources_to_delete = [resource['id'] for resource in resources if
                           resource["path"].count("/") == 1 and
                           resource["path"] != "/"]
    return resources_to_delete


def prune_paths(api_connection, api_id, resources):
    """Deletes all paths that don't exist in resources from given api

    Args:
        api_connection (ApiGatewayConnection): api gateway client
        api_id (str): id of api to work on
        paths (list(str)): list of paths from config
    """
    resources = list(resources)
    resources_to_delete = get_resources_to_delete(resources)
    for resource_to_delete in resources_to_delete:
        api_connection.delete_resource(api_id, resource_to_delete)
        resources = filter(
            lambda x: x["id"] != resource_to_delete, resources)
    return resources


def create_request_mapping_template():
    mapping_template = """
#set($params = $input.params())
#set($path = $params.path)
#set($querystring = $params.querystring)
#set($headers = $params.header)
#set($body = $input.json('$'))

{
"path" : {
    #foreach ($mapEntry in $path.entrySet())
        "$mapEntry.key":"$mapEntry.value"
        #if($velocityCount < $path.size()),#end
    #end
    },
"querystring" : {
    #foreach ($mapEntry in $querystring.entrySet())
        "$mapEntry.key":"$mapEntry.value"
        #if($velocityCount < $querystring.size()),#end
    #end
    },
"headers" : {
    #foreach ($mapEntry in $headers.entrySet())
        "$mapEntry.key":"$mapEntry.value"
        #if($velocityCount < $headers.size()),#end
    #end
    }

#if(!$body),
"body": $body
#end
}
"""

    return mapping_template


def create_integration_request(api_id, parent_id, method,
                               gateway_function_arn, creds_arn, content_type):
    mapping_templates = {}
    mapping_templates[content_type] = create_request_mapping_template()

    api_connection.create_integration(
        api_id, parent_id, method, gateway_function_arn,
        creds_arn, mapping_templates)


def package_and_upload_lambda(zip_path, code_location, api_name, function_name,
                              creds_arn, stage_name):
    # package source code if we have it
    if not zip_path:
        app_root = code_location
        if app_root[-1] != "/":
            app_root += "/"
        zipdir(app_root, "main.zip")
        zip_path = "main.zip"

    with open(zip_path) as zip_file:
        function_arn = upload(
            "PAWS-{}-{}".format(api_name, function_name),
            zip_file,
            creds_arn,
            handler_name,
            stage_name
        )

    if app_root:
        os.remove(zip_path)

    # todo:rebuild this string concat so that respects region
    gateway_function_arn = str(
        'arn:aws:apigateway:us-east-1:lambda:path'
        '/2015-03-31/functions/{0}/invocations').format(
        function_arn)

    return gateway_function_arn


def configure_route(api_connection, api_id, path, method, function_arn,
                    creds_arn, content_type, status_code, resources):
    parent_id, resources = create_resource_path(
        api_connection,
        api_id,
        path,
        resources
    )

    api_connection.create_method(
        api_id,
        parent_id,
        method
    )

    create_integration_request(
        api_id,
        parent_id,
        method,
        function_arn,
        creds_arn,
        content_type
    )

    api_connection.create_integration_response(
        api_id,
        parent_id,
        method,
        status_code
    )
    api_connection.create_method_response(
        api_id,
        parent_id,
        method,
        status_code
    )


if __name__ == '__main__':

    parser = ArgumentParser(description=str('deploy an api to AWS lambda '
                                            'and API Gateway'))
    parser.add_argument(
        "--conf", type=str, default=None, required=True,
        help="YAML or JSON swagger config describing your API")

    parser.add_argument("--publish", type=str, default=None,
                        help="name of the stage to publish to (default:dev)")

    api_group = parser.add_mutually_exclusive_group(required=True)
    api_group.add_argument(
        "--api_id", type=str, help="the api you wish to update")
    api_group.add_argument("--api_name", type=str,
                           help="name of the new api to create")

    args = parser.parse_args()

    configuration_path = args.conf
    script_directory = os.path.dirname(__file__)
    stage_name = args.publish or "dev"
    api_name = args.api_name
    api_id = args.api_id

    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    if not access_key or not secret_key:
        raise Exception("Check your AWS_ACCESS_KEY_ID and "
                        "AWS_SECRET_ACCESS_KEY environment variables")

    path_infos, config = get_config(configuration_path, script_directory)
    application_root = config["x-application-root"]

    api_connection = ApiGatewayConnection()

    # shouldn't need a third case here, parser should catch it
    if api_name:
        api_resp = api_connection.get_api_by_name(api_name)
        if not api_resp:
            api_resp = api_connection.create_api(api_name)
    elif api_id:
        api_resp = api_connection.get_api(api_id)
        api_name = api_resp["name"]

    api_id = api_resp["id"]

    resources = api_connection.get_resources(api_id)['items']

    resources = prune_paths(
        api_connection,
        api_id,
        resources
    )

    for path_info in path_infos:
        path = path_info.path_name
        zip_path = path_info.zip_path
        function_name = path_info.operation_name
        handler_name = path_info.handler_name
        creds_arn = path_info.role_arn
        method = path_info.http_method
        status_code = 200
        content_type = "application/json"
        app_root = None

        function_arn = package_and_upload_lambda(
            zip_path,
            api_name,
            function_name,
            creds_arn,
            stage_name
        )

        configure_route(
            api_connection,
            api_id,
            path,
            method,
            function_arn,
            creds_arn,
            content_type,
            status_code,
            resources
        )

    api_connection.create_deployment(api_id, stage_name)

    print("We worked on {0}".format(api_id))
    print(
        "https://{0}.execute-api.us-east-1.amazonaws.com/{1}/".
        format(api_id,
               stage_name))
