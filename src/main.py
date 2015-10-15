from lambda_client import upload
import api_gateway
import os

# this role will require the AWSLambdaRole role
creds_arn = os.environ.get('AWS_ROLE_ARN')
resp = upload("testfunction", open("main.zip"),
              creds_arn,
              "main.lambda_handler")

function_arn = resp["FunctionARN"]
# rebuild this string concat so that respects region
gateway_function_arn = str('arn:aws:apigateway:us-east-1:lambda:path'
                           '/2015-03-31/functions/{0}/invocations').format(
    function_arn)

api_resp = api_gateway.create_api("test-api")

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

create_deployment = api_gateway.create_deployment(api_id, "test")
