from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser


def get_path_segments(path):
    parts = filter(None, path.split("/"))
    return parts


def create_resource_path(api_id, parent_id, path):
    segments = get_path_segments(args.path)
    for segment in segments:
        create_resource_resp = api_connection.create_resource(
            api_id, parent_id, segment)
        resource_json = create_resource_resp.json()
        parent_id = resource_json["id"]
    return parent_id


parser = ArgumentParser(description=str('Create a single endpoint with a '
                                        'lambda function set up to serve'))
parser.add_argument('--zip', type=str, required=True,
                    help='path to the zip file to upload to lambda')
parser.add_argument("--function_name", type=str, required=True,
                    help="name of the lambda function to upload")
parser.add_argument("--api_name", type=str, required=True,
                    help="name of the new api to create")
parser.add_argument("--path", type=str, required=True,
                    help="path segment to upload to aws")
parser.add_argument("--handler", type=str, required=True,
                    help="path to your python lambda handler")

args = parser.parse_args()

# this role will require the AWSLambdaRole role
creds_arn = os.environ.get('AWS_ROLE_ARN')
access_key = os.environ.get('AWS_ACCESS_KEY_ID')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

if not creds_arn or not access_key or not secret_key:
    raise Exception("Critical information is missing")

api_connection = ApiGatewayConnection(access_key, secret_key)

resp = upload(args.function_name, open(args.zip),
              creds_arn,
              args.handler)

function_arn = resp["FunctionARN"]
# rebuild this string concat so that respects region
gateway_function_arn = str('arn:aws:apigateway:us-east-1:lambda:path'
                           '/2015-03-31/functions/{0}/invocations').format(
    function_arn)

api_resp = api_connection.create_api(args.api_name)

api_id = api_resp["api_id"]
parent_id = api_resp["parent_id"]

parent_id = create_resource_path(api_id, parent_id, args.path)

create_method_resp = api_connection.create_method(
    api_id, parent_id, "get")

create_resource_integration = api_connection.create_integration(
    api_id, parent_id, "get", gateway_function_arn,
    creds_arn)

create_integration_response = api_connection.create_integration_response(
    api_id, parent_id, "get", 200)

create_response = api_connection.create_method_response(
    api_id, parent_id, "get", 200)

create_deployment = api_connection.create_deployment(api_id, "test")
