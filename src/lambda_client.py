import boto3

client = boto3.client("lambda")


def upload(function_name, function_zip, role, handler, publish=False):
    zip_buffer = function_zip.read()
    try:
        resp = client.create_function(FunctionName=function_name,
                                      Runtime="python2.7",
                                      Role=role,
                                      Handler=handler,
                                      Code={"ZipFile": zip_buffer},
                                      Publish=publish)
    except Exception:
        resp = client.update_function_code(FunctionName=function_name,
                                           ZipFile=zip_buffer,
                                           Publish=publish)
    return resp
