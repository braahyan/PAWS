from __future__ import print_function
import boto3
from sign_request import sign_request
import os


class ApiGatewayConnection:

    def __init__(self):
        self.client = boto3.client("apigateway")
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        self.access_key = access_key
        self.secret_key = secret_key

    def create_api(self, name):
        resp = self.client.create_rest_api(name=name)
        return resp

    def get_api(self, api_id):
        resp = self.client.get_rest_api(restApiId=api_id)
        return resp

    def get_api_by_name(self, api_name):
        resp = self.client.get_rest_apis()
        return next(
            (x for x in resp['items'] if x['name'] == api_name),
            None)

    def get_resources(self, api_id):
        resp = self.client.get_resources(restApiId=api_id)
        return resp

    def delete_resource(self, api_id, resource_id):
        resp = self.client.delete_resource(
            restApiId=api_id,
            resourceId=resource_id
        )
        return resp

    def create_resource(self, api_id, parent_id, path_part):
        response = self.client.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response

    def create_method(self, api_id, resource_id, http_method):
        try:
            self.client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType="none"
            )
            return True
        except Exception:
            return False

    def create_method_response(self, api_id, resource_id,
                               http_method, status_code):
        try:
            self.client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode=str(status_code),
                responseParameters={
                },
                responseModels={
                    "application/json": "Empty"
                }
            )
            return True
        except Exception:
            return False

    def create_deployment(self, api_id, stage_name,
                          stage_description="",
                          description="",
                          cache_cluster_enabled=False,
                          cache_cluster_size="0.5"):
        response = self.client.create_deployment(
            restApiId=api_id,
            stageName=stage_name
        )
        return response

    def create_integration_response(self, api_id,
                                    resource_id, http_method, status_code,
                                    selection_pattern=None):

        url = ("/restapis/{0}/resources/{1}/methods/{2}/"
               "integration/responses/{3}").format(
            api_id,
            resource_id,
            http_method.upper(),
            status_code
        )
        return sign_request(
            self.access_key,
            self.secret_key,
            method="put",
            canonical_uri=url,
            request_body={
                "selectionPattern": selection_pattern,
                "responseParameters": {
                },
                "responseTemplates": {
                    "application/json": ""
                }
            })

    def create_integration(self, api_id, resource_id,
                           http_method, uri, credentials,
                           content_mapping_templates=None):
        if not content_mapping_templates:
            content_mapping_templates = {}

        url = "/restapis/{0}/resources/{1}/methods/{2}/integration".format(
            api_id,
            resource_id,
            http_method.upper()
        )

        resp = sign_request(
            self.access_key,
            self.secret_key,
            canonical_uri=url,
            method='put',
            request_body={
                "type": "AWS",
                "httpMethod": "POST",
                "uri": uri,
                "credentials": credentials,
                "requestParameters": {
                },
                "requestTemplates": content_mapping_templates,
                "cacheNamespace": "none",
                "cacheKeyParameters": []
            }
        )
        return resp
