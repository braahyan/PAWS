from lambda_client import upload
import api_gateway
import os
from argparse import ArgumentParser


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
resp = upload(args.function_name, open(args.zip),
              creds_arn,
              args.handler)

function_arn = resp["FunctionARN"]
# rebuild this string concat so that respects region
gateway_function_arn = str('arn:aws:apigateway:us-east-1:lambda:path'
                           '/2015-03-31/functions/{0}/invocations').format(
    function_arn)

api_resp = api_gateway.create_api(args.api_name)

api_id = api_resp["api_id"]
parent_id = api_resp["parent_id"]

create_resource_resp = api_gateway.create_resource(
    api_id, parent_id, "test")

resource_json = create_resource_resp.json()

create_method_resp = api_gateway.create_method(
    api_id, resource_json["id"], "get")

create_resource_integration = api_gateway.create_integration(
    api_id, resource_json["id"], "get", gateway_function_arn,
    creds_arn)

create_integration_response = api_gateway.create_integration_response(
    api_id, resource_json["id"], "get", 200)

create_response = api_gateway.create_method_response(
    api_id, resource_json["id"], "get", 200)

create_deployment = api_gateway.create_deployment(api_id, args.path)
