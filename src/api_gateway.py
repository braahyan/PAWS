from __future__ import print_function
from sign_request import sign_request


def create_api(name):
    resp = sign_request(method='post',
                        canonical_uri='/restapis',
                        request_body={"name": name,
                                      "cloneFrom": None,
                                      "description": None})
    body = resp.json()
    return body["self"]["restApiId"], body


def delete_api(id):
    resp = sign_request(method='delete',
                        canonical_uri="/restapis/{0}".format(id))
    return resp


def create_resource(api_id, parent_id, name):
    url = "/restapis/{0}/resources/{1}".format(api_id, parent_id)
    print(url)
    return sign_request(method='post',
                        request_body={"pathPart": name},
                        canonical_uri=url)
