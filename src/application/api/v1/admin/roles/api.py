from utils.router import AdminBlueprint
from utils.util import http_response
from utils.constant import API_LOGGER
from utils.constant import LogLevel

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Log, Role, Permission

from modules.auth import jwt

from utils.util import Paginator
import logging

JwtAuth = jwt.JwtAuth()
Logger = logging.getLogger(API_LOGGER)


@AdminBlueprint.get("/roles")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.parameter(name="id", required=False, schema={"id": "int"})
@openapi.parameter(name="role_name", required=False, schema={"role_name": "str"})
@openapi.parameter(name="page", required=False, schema={"page": "int"})
@openapi.parameter(name="page_size", required=False, schema={"page_size": "int"})
@openapi.response(status=200, content={"application/json": serializers.AdminGetRolesSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminGetRolesQuery)
@JwtAuth.permissions_authorized()
async def admin_get_roles(request: Request, query: serializers.AdminGetRolesQuery):
    roles_model = serializers.RolesModel.model_validate(query, from_attributes=True)
    roles_model = roles_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if roles_model:
        paginator = Paginator(Role.filter(**roles_model), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(Role.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    
    results = []
    for item in paginator.items:
        result = serializers.RolesModel.model_validate(item, from_attributes=True)
        permissions = [serializers.PermissionsModel.model_validate(permission, from_attributes=True) for permission in await item.permissions]
        result.permissions = permissions
        results.append(result)

    response = serializers.AdminGetRolesSuccessfullyResponse(result=results, total_items=paginator.total_items, total_pages=paginator.total_pages).model_dump()
    
    return http_response(status = 200, **response)



@AdminBlueprint.post("/roles")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminPostRolesBody.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.AdminPostRolesSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPostRolesBody)
@JwtAuth.permissions_authorized()
async def admin_post_roles(request: Request, body: serializers.AdminPostRolesBody):
    if await Role.exists(role_name=body.role_name):
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status=400, **response)
    
    new_role = Role(role_name=body.role_name)
    await new_role.save()
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - New role [{body.role_name}] is created")
    new_log = Log(user = user, api = request.uri_template, action = f"New role [{body.role_name}] is created", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPostRolesSuccessfullyResponse().model_dump()
    return http_response(status=201, **response)



@AdminBlueprint.delete("/roles")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminDeleteRolesBody.model_json_schema()})
@openapi.response(status=204, content={"application/json": serializers.AdminDeleteRolesSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is not exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminDeleteRolesBody)
@JwtAuth.permissions_authorized()
async def admin_delete_roles(request: Request, query: serializers.AdminDeleteRolesBody):
    role_model = serializers.RolesModel.model_validate(query, from_attributes=True)
    role_model = role_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if not role_model:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    roles_model = Role.filter(**role_model)
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await roles_model.delete()
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Role [{role_model}] is deleted")
    new_log = Log(user = user, api = request.uri_template, action = f"Role [{role_model}] is deleted", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminDeleteRolesSuccessfullyResponse().model_dump()
    return http_response(status = 204, **response)



@AdminBlueprint.put("/roles")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminPutRolesBody.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.AdminPutRolesSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPutRolesBody)
@JwtAuth.permissions_authorized()
async def admin_put_roles(request: Request, body: serializers.AdminPutRolesBody):
    roles_model = Role.filter(id = body.id)
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    old_role_name = await roles_model.first()
    old_role_name = old_role_name.role_name

    await roles_model.update(role_name = body.role_name)
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Role [{old_role_name}] is renamed to [{body.role_name}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Role [{old_role_name}] is renamed to [{body.role_name}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPutRolesSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)



@AdminBlueprint.post("/roles/permissions")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminPostRolesPermissionsBody.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.AdminPostRolesPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPostRolesPermissionsBody)
@JwtAuth.permissions_authorized()
async def admin_post_roles_permissions(request: Request, body: serializers.AdminPostRolesPermissionsBody):
    if body.id and body.role_name:
        roles_model = Role.filter(id=body.id, role_name=body.role_name)
    elif body.id:
        roles_model = Role.filter(id=body.id)
    elif body.role_name:
        roles_model = Role.filter(role_name=body.role_name)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)

    permissions_model = serializers.PermissionsModel.model_validate(body.permissions, from_attributes=True)
    permissions_model = permissions_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if permissions_model:
        permissions_model = Permission.filter(**permissions_model)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await permissions_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    roles_model = await roles_model.first()
    permissions_model = await permissions_model.first()

    if permissions_model in await roles_model.permissions:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await roles_model.permissions.add(permissions_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Role [{roles_model.role_name}] add permission [{permissions_model.permission_title}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Role [{roles_model.role_name}] add permission [{permissions_model.permission_title}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPostRolesPermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)



@AdminBlueprint.delete("/roles/permissions")
@openapi.summary("roles")
@openapi.description("roles")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminDeleteRolesPermissionsBody.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.AdminDeleteRolesPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminDeleteRolesPermissionsBody)
@JwtAuth.permissions_authorized()
async def admin_delete_roles_permissions(request: Request, body: serializers.AdminDeleteRolesPermissionsBody):
    if body.id and body.role_name:
        roles_model = Role.filter(id=body.id, role_name=body.role_name)
    elif body.id:
        roles_model = Role.filter(id=body.id)
    elif body.role_name:
        roles_model = Role.filter(role_name=body.role_name)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)

    permissions_model = serializers.PermissionsModel.model_validate(body.permissions, from_attributes=True)
    permissions_model = permissions_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if permissions_model:
        permissions_model = Permission.filter(**permissions_model)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await permissions_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    roles_model = await roles_model.first()
    permissions_model = await permissions_model.first()

    if permissions_model in await roles_model.permissions:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await roles_model.permissions.remove(permissions_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Role [{roles_model.role_name}] remove permission [{permissions_model.permission_title}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Role [{roles_model.role_name}] remove permission [{permissions_model.permission_title}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminDeleteRolesPermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 204, **response)