import boto


def upload(function_name, function_zip, role, handler):
    con = boto.connect_awslambda()
    con.upload_function(function_name, function_zip, "python2.7",
                        role, handler, "event")
