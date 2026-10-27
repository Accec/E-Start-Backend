from pydantic import BaseModel
from sanic import response


def http_response(code, msg="", results=None, status=200, **kwargs):
    if "result" in kwargs:
        raise TypeError("Use 'results' instead of 'result'")
    output = {"code": code, "msg": msg, "results": results}
    if kwargs:
        output.update(kwargs)
    return response.json(output, status=status)


def schema_response(schema: BaseModel, *, status=200):
    return http_response(status=status, **schema.model_dump())
