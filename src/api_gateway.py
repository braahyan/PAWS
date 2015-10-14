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


# VESTIGIAL: develop this into something useful
def get_apis():
    resp = sign_request(method='get',
                        canonical_uri='/restapis')
    return resp.json()


def get_resources(api_id):
    resp = sign_request(method='get',
                        canonical_uri='/restapis/{0}'.format(api_id))
    return resp.json()


def get_resource_info(api_id, resource_id):
    url = "/restapis/{0}/resources/{1}".format(api_id,
                                               resource_id)
    return sign_request(method="get", canonical_uri=url)


def delete_api(api_id):
    resp = sign_request(method='delete',
                        canonical_uri="/restapis/{0}".format(api_id))
    return resp.status_code == 200 or resp.status_code == 202


def create_resource(api_id, parent_id, name):
    url = "/restapis/{0}/resources/{1}".format(api_id, parent_id)
    return sign_request(method='post',
                        request_body={"pathPart": name},
                        canonical_uri=url)


def create_method(api_id, resource_id, method):
    url = "/restapis/{0}/resources/{1}/methods/{2}".format(
        api_id, resource_id, method)
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
