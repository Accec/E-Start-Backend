from utils.router import UserBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError

from utils.constant import API_LOGGER

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Role, Endpoint

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

JwtAuth = jwt.JwtAuth()

@UserBlueprint.get("/dashboard")
@openapi.summary("Dashboard")
@openapi.description("dashboard")
@openapi.secured("token")
@openapi.response(status=200, content={"application/json": serializers.UserGetDashboardSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@JwtAuth.permissions_authorized()
async def user_get_dashboard(request: Request):
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    roles = await user.roles
    
    permissions = {permission for role in roles for permission in await role.permissions.all()}
    endpoints = {endpoint for permission in permissions for endpoint in await permission.endpoints}
    
    user_info = serializers.UserGetDashboardUserModel.model_validate(user, from_attributes=True)
    roles = [serializers.UserGetDashboardUserModel.model_validate(role, from_attributes=True) for role in roles]
    serializers.UserGetDashboardResultsModel(user_info=user_info, roles=roles, )
    
    print (user, roles, permissions, endpoints)
    return http_response(status = 200, code = Successfully.code, msg = Successfully.msg)