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
    parts = filter(None, path.split(os.sep))
    return parts


def get_resource_by_path(path, resources):
    return next(
        (x for x in resources if x['path'] == path),
        None)


def get_resources_to_create(path, resources):
    """gets the resources to create for this path

    Args:
        path (str): path to create
        resources (list(str)): list of resources that have already been created

    Returns:
        (str, list(str)): the first item is a parent_id of the path to create,
                          the second is a list of path segments to create, in
                          order
    """
    cur_path = "/"
    segments = get_path_segments(path)
    parent_id = get_resource_by_path("/", resources)['id']

    resources_to_create = []

    for segment in segments:
        cur_path += segment

        previous_created_resource = get_resource_by_path(cur_path, resources)

        if not previous_created_resource:
            resources_to_create.append(segment)
        else:
            parent_id = previous_created_resource["id"]
        cur_path += "/"

    return parent_id, resources_to_create


def create_resource_path(api_connection, api_id, path):
    """creates all resources necessary for a path

    Args:
        api_connection (ApiGatewayConnection): api gateway client
        api_id (str): id of the api to operate on
        path (str): path to create

    Returns:
        str: id of the resource that was created
    """
    resources = api_connection.get_resources(api_id)

    parent_id, resources_to_create = get_resources_to_create(
        path, resources['items'])

    cur_path = "/"
    for segment in resources_to_create:
        cur_path += segment

        create_resource_resp = api_connection.create_resource(
            api_id, parent_id, segment)
        resource_json = create_resource_resp

        parent_id = resource_json["id"]
        cur_path += "/"

    return parent_id


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
                               gateway_function_arn, creds_arn, content_type,
                               parameters):
    mapping_templates = {}
    mapping_templates[content_type] = create_request_mapping_template()

    api_connection.create_integration(
        api_id, parent_id, method, gateway_function_arn,
        creds_arn, mapping_templates)


def is_substring_of_path(needle, haystack):
    """returns true if the needle is a substring
       of anything in the haystack

    Args:
        needle (str): String to find in haystack
        haystack (list(str)): Collection to search through

    Returns:
        bool: Description
    """
    for x in haystack:
        if x.find(needle) == 0:
            return False
    return True


def get_resources_to_delete(resources, paths):
    """returns a list of all resources to delete

    Args:
        resources (list(dict)): resources to compare to the paths
        paths (list(str)): paths from the config file

    Returns:
        list(str): list of ids of resources to remove
    """
    sorted_resources = reversed(sorted(resources,
                                       key=lambda x: x["path"].count("/")))
    resources_to_delete = [resource['id']
                           for resource
                           in sorted_resources
                           # is substring of path determines if the
                           # current path is a substring of any of the other
                           # paths passed in
                           if is_substring_of_path(resource["path"], paths)]
    return resources_to_delete


def prune_nonexistent_paths(api_connection, api_id, paths):
    """Deletes all paths that don't exist in paths from given api

    Args:
        api_connection (ApiGatewayConnection): api gateway client
        api_id (str): id of api to work on
        paths (list(str)): list of paths from config
    """
    resources = api_connection.get_resources(api_id)['items']
    resources_to_delete = get_resources_to_delete(resources, paths)
    for resource_to_delete in resources_to_delete:
        api_connection.delete_resource(api_id, resource_to_delete)


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

load_str = args.conf
script_directory = os.path.dirname(__file__)
stage_name = args.publish or "dev"
is_publishing = args.publish is not None
api_name = args.api_name
api_id = args.api_id

access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

if not access_key or not secret_key:
    raise Exception("Critical information is missing")

path_infos, config = get_config(load_str, script_directory)
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


prune_nonexistent_paths(api_connection, api_id, [x[0] for x in path_infos])


for path_info in path_infos:
    path = path_info[0]
    zip_path = path_info[1]
    function_name = path_info[2]
    handler_name = path_info[3]
    creds_arn = path_info[4]
    method = path_info[5]
    parameters = path_info[6]
    status_code = 200
    content_type = "application/json"
    app_root = None

    # package source code if we have it
    if not zip_path:
        app_root = application_root
        if app_root[-1] != "/":
            app_root += "/"
        zipdir(app_root, "main.zip")
        zip_path = "main.zip"

    with open(zip_path) as zip_file:
        lambda_resp = upload("PAWS-{0}-{1}".format(api_name, function_name),
                             zip_file,
                             creds_arn,
                             handler_name,
                             is_publishing)

    if app_root:
        os.remove(zip_path)

    function_arn = lambda_resp["FunctionArn"]
    # todo:rebuild this string concat so that respects region
    gateway_function_arn = str('arn:aws:apigateway:us-east-1:lambda:path'
                               '/2015-03-31/functions/{0}/invocations').format(
        function_arn)

    parent_id = create_resource_path(
        api_connection, api_id, path)

    api_connection.create_method(
        api_id, parent_id, method)

    create_integration_request(api_id, parent_id, method,
                               gateway_function_arn, creds_arn, content_type,
                               parameters)

    api_connection.create_integration_response(
        api_id, parent_id, method, status_code)
    api_connection.create_method_response(
        api_id, parent_id, method, status_code)
    api_connection.create_deployment(api_id, stage_name)


print("We worked on {0}".format(api_id))
