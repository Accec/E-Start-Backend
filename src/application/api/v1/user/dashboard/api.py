from utils.router import UserBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError

from utils.constant import API_LOGGER

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
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@JwtAuth.permissions_authorized()
async def user_get_dashboard(request: Request):
    
    return http_response(status = 200, code = Successfully.code, msg = Successfully.msg)