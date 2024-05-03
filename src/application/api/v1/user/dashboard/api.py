from utils.router import UserBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Log, Role

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

JwtAuth = jwt.JwtAuth()

@UserBlueprint.post("/dashboard")
@openapi.summary("Dashboard")
@openapi.description("dashboard")
@openapi.secured("token")
@openapi.response(status=200, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=500, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema(), "application/json": serializers.AccountOrPasswordInvalidResponse.model_json_schema()}, description="Args invalid | The account or password invalid")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@JwtAuth.authorized("edit")
async def get_dashboard(request: Request):
    
    return http_response(status = 200, code = Successfully.code, msg = Successfully.msg)