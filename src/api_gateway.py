from __future__ import print_function
from sign_request import sign_request
import os


class ApiGatewayConnection:

    def __init__(self, access_key=None, secret_key=None):

        if not access_key or not secret_key:
            access_key = os.environ.get('AWS_ACCESS_KEY_ID', access_key)
            secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', secret_key)

        self.access_key = access_key
        self.secret_key = secret_key

    def create_api(self, name):
        resp = sign_request(self.access_key,
                            self.secret_key,
                            method='post',
                            canonical_uri='/restapis',
                            request_body={"name": name,
                                          "cloneFrom": None,
                                          "description": None})
        return resp

    def get_apis(self):
        resp = sign_request(self.access_key,
                            self.secret_key,
                            method='get',
                            canonical_uri='/restapis')
        return resp

    def get_api(self, api_id):
        resp = sign_request(self.access_key,
                            self.secret_key,
                            method='get',
                            canonical_uri='/restapis/{0}'.format(api_id))
        return resp

    def delete_api(self, api_id):
        resp = sign_request(self.access_key,
                            self.secret_key,
                            method='delete',
                            canonical_uri="/restapis/{0}".format(api_id))
        return resp

    def get_resources(self, api_id):
        resp = sign_request(self.access_key,
                            self.secret_key,
                            method='get',
                            canonical_uri='/restapis/{0}/resources'.format(
                                api_id))
        return resp

    def get_resource(self, api_id, resource_id):
        url = "/restapis/{0}/resources/{1}".format(api_id,
                                                   resource_id)
        return sign_request(self.access_key,
                            self.secret_key,
                            method="get", canonical_uri=url)

    def create_resource(self, api_id, parent_id, path_part):
        url = "/restapis/{0}/resources/{1}".format(api_id, parent_id)
        return sign_request(self.access_key,
                            self.secret_key,
                            method='post',
                            request_body={"pathPart": path_part},
                            canonical_uri=url)

    def create_method(self, api_id, resource_id, http_method):
        url = "/restapis/{0}/resources/{1}/methods/{2}".format(
            api_id, resource_id, http_method.upper())
        return sign_request(self.access_key,
                            self.secret_key,
                            method='put',
                            request_body={
                                "authorizationType": "none",
                                "apiKeyRequired": False,
                                "requestParameters": {
                                },
                                "requestModels": {
                                }
                            },
                            canonical_uri=url)

    def get_method(self, api_id, resource_id, method):
        url = "/restapis/{0}/resources/{1}/methods/{2}".format(
            api_id, resource_id, method.upper())
        return sign_request(self.access_key,
                            self.secret_key,
                            method="get", canonical_uri=url)

    def create_integration(self, api_id, resource_id,
                           http_method, uri, credentials):
        url = str(
            "/restapis/{0}/resources/"
            "{1}/methods/{2}/integration"
        ).format(api_id, resource_id, http_method.upper())
        return sign_request(self.access_key,
                            self.secret_key,
                            canonical_uri=url, method='put', request_body={
                                "type": "AWS",
                                "httpMethod": "POST",
                                "uri": uri,
                                "credentials": credentials,
                                "requestParameters": {
                                },
                                "requestTemplates": {
                                },
                                "cacheNamespace": "none",
                                "cacheKeyParameters": []
                            })

    def get_integration(self, api_id, resource_id, http_method):
        url = str(
            "/restapis/{0}/resources/"
            "{1}/methods/{2}/integration"
        ).format(api_id, resource_id, http_method.upper())
        return sign_request(self.access_key,
                            self.secret_key,
                            canonical_uri=url, method="get")

    def create_method_response(self, api_id, resource_id,
                               http_method, status_code):
        url = "/restapis/{0}/resources/{1}/methods/{2}/responses/{3}".format(
            api_id, resource_id, http_method.upper(), status_code)
        return sign_request(self.access_key,
                            self.secret_key,
                            method="put",
                            canonical_uri=url,
                            request_body={
                                "responseParameters": {
                                },
                                "responseModels": {
                                    "application/json": "Empty"
                                }
                            })

    def get_method_response(self, api_id, resource_id,
                            http_method, status_code):
        url = "/restapis/{0}/resources/{1}/methods/{2}/responses/{3}".format(
            api_id, resource_id, http_method.upper(), status_code)
        return sign_request(self.access_key,
                            self.secret_key,
                            method="get",
                            canonical_uri=url)

    def create_integration_response(self, api_id,
                                    resource_id, http_method, status_code):
        url = str("/restapis/{0}/resources/{1}/methods/"
                  "{2}/integration/responses/{3}").format(
            api_id, resource_id, http_method.upper(), status_code)
        return sign_request(self.access_key,
                            self.secret_key,
                            method="put",
                            canonical_uri=url,
                            request_body={
                                "selectionPattern": None,
                                "responseParameters": {
                                },
                                "responseTemplates": {
                                    "application/json": ""
                                }
                            })

    def create_deployment(self, api_id, stage_name,
                          stage_description="",
                          description="",
                          cache_cluster_enabled=False,
                          cache_cluster_size="0.5"):
        url = "/restapis/{0}/deployments".format(api_id)
        return sign_request(self.access_key,
                            self.secret_key,
                            method="post",
                            canonical_uri=url,
                            request_body={
                                "stageName": stage_name,
                                "stageDescription": stage_description,
                                "description": description,
                                "cacheClusterEnabled": cache_cluster_enabled,
                                "cacheClusterSize": cache_cluster_size
                            })
