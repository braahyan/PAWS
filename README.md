Pardon my mess, PAWS is still in heavy development.




PAWS uses a config language that is an extension of swagger. 

The AWS role below must have a trust policy set up that has a trust relationship with both Lambda and API Gateway, additionally, it should have the "lambda:InvokeFunction" permission associated with it.

Here is a very simple PAWS yaml example:

```yaml
swagger: '2.0'
info:
  version: 1.0.0
  title: PAWS TODO
  description: A sample API that implements a simple todo app for PAWS
  termsOfService: 'http://helloreverb.com/terms/'
  contact:
    name: Bryan Pedlar
    email: foo@example.com
    url: 'http://thrivehive.com'
  license:
    name: MIT
    url: 'http://opensource.org/licenses/MIT'
host: todo.thrivehive.com
schemes:
  - https
consumes:
  - application/json
produces:
  - application/json
x-application-root: src
paths:
  /todos:
    get:
      x-handler-name: main.get_todos
      x-role-arn: __your_lambda_api_gateway_role-arn_here__
      description: Returns all todos from the system that the user has access to
      operationId: getTodos
      parameters:
        - name: limit
          in: query
          description: maximum number of results to return
          required: false
          type: integer
          format: int32
      responses:
        '200':
          description: todo response
          schema:
            type: array
            items:
              $ref: '#/definitions/todo'
        default:
          description: unexpected error
          schema:
            $ref: '#/definitions/errorModel'
definitions:
  todo:
    type: object
    required:
      - id
      - name
    properties:
      id:
        type: string
      name:
        type: string
  errorModel:
    type: object
    required:
      - code
      - message
    properties:
      code:
        type: integer
        format: int32
      message:
        type: string

```

PAWS expects these environment variables to be available:

```
export AWS_ACCESS_KEY_ID=__YOUR_ACCESS_KEY_HERE__
export AWS_SECRET_ACCESS_KEY=__YOUR_SECRET_ACCESS_KEY_HERE__
```

The AWS access key needs permissions to administer the account. Right now I have only tested with the administrator access role, but will be updating this as I gain a greater understanding of the AWS permissions model.

example main invocation.
python main.py --api_name foobar --conf swagger.yaml (--publish your_stage_name)

*Note that the first time you run this, it will create the api, the second time, it will search for the API by name*


example update invocation.
python main.py --api_id 782gr8gmnb --conf swagger.yaml (--publish your_stage_name)


*Roadmap*

- CodeGen of Python Models
- Python Validation Framework using Swagger definition
- Static asset hosting on S3/CloudFront
- domain management via Route53
- support for AWSM modules
