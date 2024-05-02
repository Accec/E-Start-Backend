from utils.router import UserBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError

from sanic import request
from sanic_ext import validate, openapi

from . import serializers

@UserBlueprint.post("/login")
@openapi.summary("Login")
@openapi.description("Login")
@openapi.body({"application/json": serializers.LoginPayloads.model_json_schema()})
@openapi.response(status=200, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.LoginPayloads)
async def post_login(request: request, body: serializers.LoginPayloads):
    
    return http_response(status = 200, code = Successfully.code, msg = Successfully.msg)