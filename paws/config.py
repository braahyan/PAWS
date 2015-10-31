import json
import yaml
from jsonschema import validate


def validate_paws_spec(spec, schema_object):
    validate(spec, schema_object)


def load_config_file(load_str):
    with open(load_str) as foo:
        body = foo.read()
    if "yaml" in load_str:
        # hack to make schema work, likely related to unicode
        spec = json.loads(json.dumps(yaml.load(body)))
    elif "json" in load_str:
        spec = json.loads(body)
    return spec


def load_swagger_schema(script_directory):
    if script_directory:
        script_directory += "/"
    with open(script_directory + "schema.json") as schema_file:
        schema_text = schema_file.read()
        schema_object = json.loads(schema_text)
        return schema_object


def get_config(load_str, script_directory):
    schema_object = load_swagger_schema(script_directory)
    config = load_config_file(load_str)
    validate_paws_spec(config, schema_object)
    path_infos = []
    for path_name in config["paths"]:
        for method in config["paths"][path_name].keys():
            method_info = config["paths"][path_name][method]
            path_infos.append(
                [path_name,
                 method_info.get("x-zip-path", None),
                 method_info["operationId"],
                 method_info["x-handler-name"],
                 method_info["x-role-arn"],
                 method.upper(),
                 method_info["parameters"]])
    return path_infos, config
