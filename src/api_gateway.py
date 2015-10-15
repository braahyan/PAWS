from __future__ import print_function
from sign_request import sign_request


def create_api(name):
    resp = sign_request(method='post',
                        canonical_uri='/restapis',
                        request_body={"name": name,
                                      "cloneFrom": None,
                                      "description": None})
    body = resp.json()
    return {"api_id": body["resourceCreate"]["restApiId"],
            "parent_id": body["resourceCreate"]["parentId"]}


def get_apis():
    resp = sign_request(method='get',
                        canonical_uri='/restapis')
    return resp.json()


def get_api(api_id):
    resp = sign_request(method='get',
                        canonical_uri='/restapis/{0}'.format(api_id))
    return resp.json()


def delete_api(api_id):
    resp = sign_request(method='delete',
                        canonical_uri="/restapis/{0}".format(api_id))
    return resp.status_code == 200 or resp.status_code == 202


def get_resources(api_id):
    resp = sign_request(method='get',
                        canonical_uri='/restapis/{0}/resources'.format(api_id))
    return resp.json()


def get_resource(api_id, resource_id):
    url = "/restapis/{0}/resources/{1}".format(api_id,
                                               resource_id)
    return sign_request(method="get", canonical_uri=url)


def create_resource(api_id, parent_id, path_part):
    url = "/restapis/{0}/resources/{1}".format(api_id, parent_id)
    return sign_request(method='post',
                        request_body={"pathPart": path_part},
                        canonical_uri=url)


def create_method(api_id, resource_id, http_method):
    url = "/restapis/{0}/resources/{1}/methods/{2}".format(
        api_id, resource_id, http_method.upper())
    return sign_request(method='put',
                        request_body={
                            "authorizationType": "none",
                            "apiKeyRequired": False,
                            "requestParameters": {
                            },
                            "requestModels": {
                            }
                        },
                        canonical_uri=url)


def get_method(api_id, resource_id, method):
    url = "/restapis/{0}/resources/{1}/methods/{2}".format(
        api_id, resource_id, method.upper())
    return sign_request(method="get", canonical_uri=url)


def create_integration(api_id, resource_id, http_method, uri, credentials):
    url = str(
        "/restapis/{0}/resources/"
        "{1}/methods/{2}/integration"
    ).format(api_id, resource_id, http_method.upper())
    return sign_request(canonical_uri=url, method='put', request_body={
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


def get_integration(api_id, resource_id, http_method):
    url = str(
        "/restapis/{0}/resources/"
        "{1}/methods/{2}/integration"
    ).format(api_id, resource_id, http_method.upper())
    return sign_request(canonical_uri=url, method="get")


def create_method_response(api_id, resource_id, http_method, status_code):
    url = "/restapis/{0}/resources/{1}/methods/{2}/responses/{3}".format(
        api_id, resource_id, http_method.upper(), status_code)
    return sign_request(method="put",
                        canonical_uri=url,
                        request_body={
                            "responseParameters": {
                            },
                            "responseModels": {
                                "application/json": "Empty"
                            }
                        })


def get_method_response(api_id, resource_id, http_method, status_code):
    url = "/restapis/{0}/resources/{1}/methods/{2}/responses/{3}".format(
        api_id, resource_id, http_method.upper(), status_code)
    return sign_request(method="get",
                        canonical_uri=url)


def create_integration_response(api_id, resource_id, http_method, status_code):
    url = str("/restapis/{0}/resources/{1}/methods/"
              "{2}/integration/responses/{3}").format(
        api_id, resource_id, http_method.upper(), status_code)
    return sign_request(method="put",
                        canonical_uri=url,
                        request_body={
                            "selectionPattern": None,
                            "responseParameters": {
                            },
                            "responseTemplates": {
                                "application/json": ""
                            }
                        })


def create_deployment(api_id, stage_name,
                      stage_description="",
                      description="",
                      cache_cluster_enabled=False,
                      cache_cluster_size="0.5"):
    url = "/restapis/{0}/deployments".format(api_id)
    return sign_request(method="post",
                        canonical_uri=url,
                        request_body={
                            "stageName": stage_name,
                            "stageDescription": stage_description,
                            "description": description,
                            "cacheClusterEnabled": cache_cluster_enabled,
                            "cacheClusterSize": cache_cluster_size
                        })
