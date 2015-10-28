from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser
import json
import yaml
from jsonschema import validate
import zipfile


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

api_group = parser.add_mutually_exclusive_group(required=True)
api_group.add_argument(
    "--api_id", type=str, help="the api you wish to update")
api_group.add_argument("--api_name", type=str,
                       help="name of the new api to create")

args = parser.parse_args()

load_str = args.conf
script_directory = os.path.dirname(__file__)
if script_directory:
    script_directory += "/"
with open(script_directory + "schema.json") as schema_file:
    schema_text = schema_file.read()
    schema_object = json.loads(schema_text)
with open(load_str) as foo:
    body = foo.read()
if "yaml" in load_str:
    # hack to make schema work, likely related to unicode
    spec = json.loads(json.dumps(yaml.load(body)))
elif "json" in load_str:
    spec = json.loads(body)
validate(spec, schema_object)
produces = spec["produces"]  # this is a list
path_infos = []
for path_name in spec["paths"]:
    for method in spec["paths"][path_name].keys():
        path_infos.append(
            [path_name,
             spec["paths"][path_name][method][
                 "x-zip-path"] if "x-zip-path"
             in spec["paths"][path_name][method] else None,
             spec["paths"][path_name][method]["operationId"],
             spec["paths"][path_name][method]["x-handler-name"],
             spec["paths"][path_name][method]["x-role-arn"],
             method.upper(),
             spec["paths"][path_name][method]["parameters"]])


# this role will require the AWSLambdaRole role
access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

if not access_key or not secret_key:
    raise Exception("Critical information is missing")

api_connection = ApiGatewayConnection()

# shouldn't need a third case here, parser should catch it
if args.api_name:
    api_resp = api_connection.create_api(args.api_name)
elif args.api_id:
    api_resp = api_connection.get_api(args.api_id)

api_id = api_resp["id"]


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
    stage_name = "test"
    app_root = None

    if not zip_path:
        app_root = spec['x-application-root']
        if app_root[-1] != "/":
            app_root += "/"
        zipdir(app_root, "main.zip")
        zip_path = "main.zip"

    with open(zip_path) as zip_file:
        resp = upload("PAWS-{0}-{1}".format(stage_name, function_name),
                      zip_file,
                      creds_arn,
                      handler_name)

    if app_root:
        os.remove(zip_path)

    function_arn = resp["FunctionARN"]
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
