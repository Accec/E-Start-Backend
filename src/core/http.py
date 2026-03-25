from pydantic import BaseModel
from sanic import response


def http_response(code, msg="", result=None, status=200, **kwargs):
    if result is None and "result" in kwargs:
        result = kwargs.pop("result")
    if "results" in kwargs:
        raise TypeError("Use 'result' instead of 'results'")
    output = {"code": code, "msg": msg, "result": result}
    if kwargs:
        output.update(kwargs)
    return response.json(output, status=status)


def schema_response(schema: BaseModel, *, status=200):
    return http_response(status=status, **schema.model_dump())
