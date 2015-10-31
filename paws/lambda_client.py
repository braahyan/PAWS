import boto3

client = boto3.client("lambda")


def upload(function_name, function_zip, role, handler, alias_name=None):
    zip_buffer = function_zip.read()
    try:
        resp = client.create_function(FunctionName=function_name,
                                      Runtime="python2.7",
                                      Role=role,
                                      Handler=handler,
                                      Code={"ZipFile": zip_buffer},
                                      Publish=True)
    except Exception:
        resp = client.update_function_code(FunctionName=function_name,
                                           ZipFile=zip_buffer,
                                           Publish=True)
    if alias_name:
        try:
            resp = client.create_alias(
                FunctionName=resp["FunctionName"],
                Name=alias_name,
                FunctionVersion=resp["Version"]
            )
        except Exception:
            resp = client.update_alias(
                FunctionName=resp["FunctionName"],
                Name=alias_name,
                FunctionVersion=resp["Version"]
            )
        return resp["AliasArn"]
    return resp["FunctionArn"]
