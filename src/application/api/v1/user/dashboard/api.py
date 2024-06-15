from utils.router import UserBlueprint
from utils.util import http_response

from sanic.request import Request

from . import serializers
from models import User

from modules.auth import jwt

JwtAuth = jwt.JwtAuth()

@UserBlueprint.get("/dashboard")
@JwtAuth.permissions_authorized()
async def user_get_dashboard(request: Request):
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    roles = await user.roles
    
    permissions = {permission for role in roles for permission in await role.permissions.all()}
    endpoints = {endpoint for permission in permissions for endpoint in await permission.endpoints}
    
    permissions = [serializers.UserGetDashboardPermissionsModel.model_validate(permission, from_attributes=True) for permission in permissions]
    endpoints = [serializers.UserGetDashboardEndpointsModel.model_validate(endpoint, from_attributes=True) for endpoint in endpoints]
    
    user_info = serializers.UserGetDashboardUserModel.model_validate(user, from_attributes=True)
    roles = [serializers.UserGetDashboardRolesModel.model_validate(role, from_attributes=True) for role in roles]
    
    result = serializers.UserGetDashboardResultsModel(user_info=user_info, roles=roles, endpoints=endpoints, permissions=permissions)

    response = serializers.UserGetDashboardSuccessfullyResponse(results=result).model_dump()
    
    return http_response(status = 200, **response)