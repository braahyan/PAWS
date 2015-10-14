from upload_lambda import upload


upload("testfunction", open("main.zip"),
       "arn:aws:iam::448068919249:role/lambda_basic_execution",
       "main.lambda_handler")
