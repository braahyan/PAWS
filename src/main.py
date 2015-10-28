from __future__ import print_function
from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser
import zipfile
from config import get_config


def zipdir(path, out_path):
    with zipfile.ZipFile(out_path, 'w') as ziph:
        for root, dirs, files in os.walk(path):
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(path):]  # XXX: relative path
                ziph.write(absfn, zfn)
    return out_path


def get_path_segments(path):
    parts = filter(None, path.split(os.sep))
    return parts


def create_resource_path(api_connection, api_id, path):
    segments = get_path_segments(path)
    resources = api_connection.get_resources(api_id)

    parent_id = next(
        (x for x in resources['items'] if x['path'] == '/'),
        None)['id']

    cur_path = "/"
    for segment in segments:
        cur_path += segment
        # see if we've already created the endpoint we're
        # looking for
        previous_created_resource = next(
            (x for x in resources['items'] if x['path'] == cur_path
             and x['parentId'] == parent_id), None)

        if previous_created_resource:
            resource_json = previous_created_resource
        else:
            create_resource_resp = api_connection.create_resource(
                api_id, parent_id, segment)
            resource_json = create_resource_resp

        parent_id = resource_json["id"]
        cur_path += "/"

    return parent_id


def create_request_mapping_template():
    mapping_template = """#set($params = $input.params())
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

    #if("$!body" != ""),
"body": $body
#end
}"""

    return mapping_template


def create_integration_request(api_id, parent_id, method,
                               gateway_function_arn, creds_arn, content_type,
                               parameters):
    mapping_templates = {}
    mapping_templates[content_type] = create_request_mapping_template()

    api_connection.create_integration(
        api_id, parent_id, method, gateway_function_arn,
        creds_arn, mapping_templates)


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

# this role will require the AWSLambdaRole role
access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

if not access_key or not secret_key:
    raise Exception("Critical information is missing")

api_connection = ApiGatewayConnection()

# shouldn't need a third case here, parser should catch it
if api_name:
    api_resp = api_connection.create_api(args.api_name)
elif args.api_id:
    api_resp = api_connection.get_api(args.api_id)
    api_name = api_resp["name"]

api_id = api_resp["id"]

path_infos, config = get_config(load_str, script_directory)
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

    if not zip_path:
        app_root = config['x-application-root']
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
    # rebuild this string concat so that respects region
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
