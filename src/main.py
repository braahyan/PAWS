from lambda_client import upload
from api_gateway import ApiGatewayConnection
import os
from argparse import ArgumentParser


def get_path_segments(path):
    parts = filter(None, path.split(os.sep))
    return parts


def create_resource_path(api_connection, api_id, parent_id, path):
    segments = get_path_segments(args.path)
    resources = api_connection.get_resources(api_id)

    for segment in segments:
        
        previous_created_resource = next(
            (x for x in resources['item'] if x['pathPart'] == segment
            and x['parentId'] == parent_id)
        , None)

        if previous_created_resource:
            # get child of current parent to find this one
            resource_json = previous_created_resource
        else:
            create_resource_resp = api_connection.create_resource(
                api_id, parent_id, segment)
            resource_json = create_resource_resp.json()
        
        parent_id = resource_json["id"]

    return parent_id


def create_integrations_and_responses(api_connection, api_id, parent_id, method="get", status_code=200):
    create_method_resp = api_connection.create_method(
        api_id, parent_id, method)
    create_resource_integration = api_connection.create_integration(
        api_id, parent_id, method, gateway_function_arn,
        creds_arn)
    create_integration_response = api_connection.create_integration_response(
        api_id, parent_id, method, status_code)
    create_response = api_connection.create_method_response(
        api_id, parent_id, method, status_code)
    create_deployment = api_connection.create_deployment(api_id, "test")


parser = ArgumentParser(description=str('Create a single endpoint with a '
                                        'lambda function set up to serve'))
parser.add_argument('--zip', type=str, required=True,
                    help='path to the zip file to upload to lambda')
parser.add_argument("--function_name", type=str, required=True,
                    help="name of the lambda function to upload")
parser.add_argument("--path", type=str, required=True,
                    help="path segment to upload to aws")
parser.add_argument("--handler", type=str, required=True,
                    help="path to your python lambda handler")
group = parser.add_mutually_exclusive_group()
group.add_argument("--api_id", type=str, help="the api you wish to update")
group.add_argument("--api_name", type=str,
                   help="name of the new api to create")

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


# shouldn't need a third case here, parser should catch it
if args.api_name:
    api_resp = api_connection.create_api(args.api_name)
elif args.api_id:
    api_resp = api_connection.get_api(args.api_id)

api_id = api_resp["api_id"]
parent_id = api_resp["parent_id"]

parent_id = create_resource_path(api_connection, api_id, parent_id, args.path)

create_integrations_and_responses(api_connection, api_id, parent_id)

print("We worked on {0}".format(api_id))
