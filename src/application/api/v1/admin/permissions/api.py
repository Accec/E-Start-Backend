from utils.router import AdminBlueprint
from utils.util import http_response
from utils.constant import API_LOGGER
from utils.constant import LOG_LEVEL_MIDIUM

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Log, Role, Permission

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

from utils.util import Paginator
import logging

JwtAuth = jwt.JwtAuth()
Logger = logging.getLogger(API_LOGGER)


@AdminBlueprint.get("/permissions")
@openapi.summary("permissions")
@openapi.description("permissions")
@openapi.secured("token")
@openapi.response(status=200, content={"application/json": serializers.AdminGetPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminGetPermissionsQuery)
@JwtAuth.permissions_authorized()
async def admin_get_permissions(request: Request, query: serializers.AdminGetPermissionsQuery):
    permissions_model = serializers.PermissionsModel.model_validate(query, from_attributes=True)
    permissions_model = permissions_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if permissions_model:
        paginator = Paginator(Permission.filter(**permissions_model), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(Permission.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    
    results = []
    for item in paginator.items:
        result = serializers.PermissionsModel.model_validate(item, from_attributes=True)
        results.append(result)

    response = serializers.AdminGetPermissionsSuccessfullyResponse(result=results, total_items=paginator.total_items, total_pages=paginator.total_pages).model_dump()
    
    return http_response(status = 200, **response)



@AdminBlueprint.post("/permissions")
@openapi.summary("permissions")
@openapi.description("permissions")
@openapi.secured("token")
@openapi.response(status=201, content={"application/json": serializers.AdminPostPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPostPermissionsBody)
@JwtAuth.permissions_authorized()
async def admin_post_permissions(request: Request, body: serializers.AdminPostPermissionsBody):
    if await Permission.exists(permission_title=body.permission_title):
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status=400, **response)
    
    new_permission = Permission(permission_title=body.permission_title)
    await new_permission.save()
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - New permission [{body.permission_title}] is created")
    new_log = Log(user = user, api = request.uri_template, action = f"New permission [{body.permission_title}] is created", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()

    response = serializers.AdminPostPermissionsSuccessfullyResponse().model_dump()
    return http_response(status=201, **response)



@AdminBlueprint.delete("/permissions")
@openapi.summary("permissions")
@openapi.description("permissions")
@openapi.secured("token")
@openapi.response(status=204, content={"application/json": serializers.AdminDeletePermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is not exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminDeletePermissionsQuery)
@JwtAuth.permissions_authorized()
async def admin_delete_permissions(request: Request, query: serializers.AdminDeletePermissionsQuery):
    permission_model = serializers.PermissionsModel.model_validate(query, from_attributes=True)
    permission_model = permission_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if not permission_model:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    permissions_model = Permission.filter(**permission_model)
    if not await permissions_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await permissions_model.delete()
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Permission [{permission_model}] is deleted")
    new_log = Log(user = user, api = request.uri_template, action = f"Permission [{permission_model}] is deleted", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()

    response = serializers.AdminDeletePermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 204, **response)



@AdminBlueprint.put("/permissions")
@openapi.summary("permissions")
@openapi.description("permissions")
@openapi.secured("token")
@openapi.response(status=201, content={"application/json": serializers.AdminPutPermissionsBody.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPutPermissionsBody)
@JwtAuth.permissions_authorized()
async def admin_put_permissions(request: Request, body: serializers.AdminPutPermissionsBody):
    permission_model = Permission.filter(id = body.id)
    if not await permission_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    old_permission_title = await permission_model.first()
    old_permission_title = old_permission_title.permission_title

    await permission_model.update(permission_title = body.permission_title)
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Permission [{old_permission_title}] is renamed to [{body.permission_title}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Permission [{old_permission_title}] is renamed to [{body.permission_title}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()

    response = serializers.AdminPutPermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)