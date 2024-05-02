from utils.response import Successfully, ArgsInvalidError, RateLimitError
from utils.router import UserBlueprint
from utils.util import http_response
from sanic_ext import validate, openapi
from sanic_ext import serializer

from sanic import request

from . import serializers
from models import User

@UserBlueprint.post("/regitser")
@openapi.summary("Register")
@openapi.description("Register")
@openapi.body({"application/json": serializers.RegisterPayloads})
@openapi.response(status=201, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.RegisterPayloads)
async def post_register(request: request, body: serializers.RegisterPayloads):
    body.account
    return http_response(Successfully.code, Successfully.msg)