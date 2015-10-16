from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser


def get_path_segments(path):
    parts = filter(None, path.split(os.sep))
    return parts


def create_resource_path(api_connection, api_id, parent_id, path):
    segments = get_path_segments(path)
    resources = api_connection.get_resources(api_id)

    for segment in segments:

        # see if we've already created the endpoint we're
        # looking for
        previous_created_resource = next(
            (x for x in resources['item'] if x['pathPart'] == segment
             and x['parentId'] == parent_id), None)

        if previous_created_resource:
            resource_json = previous_created_resource
        else:
            create_resource_resp = api_connection.create_resource(
                api_id, parent_id, segment)
            resource_json = create_resource_resp.json()

        parent_id = resource_json["id"]

    return parent_id


def create_integrations_and_responses(api_connection, api_id, parent_id,
                                      gateway_function_arn, method="get",
                                      status_code=200):
    api_connection.create_method(
        api_id, parent_id, method)
    api_connection.create_integration(
        api_id, parent_id, method, gateway_function_arn,
        creds_arn)
    api_connection.create_integration_response(
        api_id, parent_id, method, status_code)
    api_connection.create_method_response(
        api_id, parent_id, method, status_code)
    api_connection.create_deployment(api_id, "test")


parser = ArgumentParser(description=str('Create a single endpoint with a '
                                        'lambda function set up to serve'))
parser.add_argument("--path", nargs=5,
                    metavar=('PATH_NAME', 'ZIP_PATH',
                             'FUNCTION_NAME', 'HANDLER_NAME', 'CREDS_ARN'),
                    type=str, required=True, default=[],
                    help="path segment to upload to aws", action='append')

group = parser.add_mutually_exclusive_group()
group.add_argument("--api_id", type=str, help="the api you wish to update")
group.add_argument("--api_name", type=str,
                   help="name of the new api to create")

args = parser.parse_args()

# this role will require the AWSLambdaRole role
access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

if not access_key or not secret_key:
    raise Exception("Critical information is missing")

api_connection = ApiGatewayConnection(access_key, secret_key)

# shouldn't need a third case here, parser should catch it
if args.api_name:
    api_resp = api_connection.create_api(args.api_name)
elif args.api_id:
    api_resp = api_connection.get_api(args.api_id)

for path_info in args.path:
    path = path_info[0]
    zip_path = path_info[1]
    function_name = path_info[2]
    handler_name = path_info[3]
    creds_arn = path_info[4]

    resp = upload(function_name, open(zip_path),
                  creds_arn,
                  handler_name)
    function_arn = resp["FunctionARN"]
    # rebuild this string concat so that respects region
    gateway_function_arn = str('arn:aws:apigateway:us-east-1:lambda:path'
                               '/2015-03-31/functions/{0}/invocations').format(
        function_arn)
    api_id = api_resp["api_id"]
    parent_id = api_resp["parent_id"]

    parent_id = create_resource_path(
        api_connection, api_id, parent_id, path)

    create_integrations_and_responses(
        api_connection, api_id, parent_id, gateway_function_arn)

print("We worked on {0}".format(api_id))
