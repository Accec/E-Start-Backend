from utils.router import AdminBlueprint
from utils.util import http_response
from utils.constant import API_LOGGER
from utils.constant import LOG_LEVEL_MIDIUM

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Log, Endpoint, Permission

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

from utils.util import Paginator

import logging

JwtAuth = jwt.JwtAuth()
Logger = logging.getLogger(API_LOGGER)

@AdminBlueprint.get("/endpoints")
@openapi.summary("endpoints")
@openapi.description("endpoints")
@openapi.secured("token")
@openapi.parameter(name="id", required=False, schema={"id": "int"})
@openapi.parameter(name="endpoint", required=False, schema={"endpoint": "str"})
@openapi.parameter(name="page", required=False, schema={"page": "int"})
@openapi.parameter(name="page_size", required=False, schema={"page_size": "int"})
@openapi.response(status=200, content={"application/json": serializers.AdminGetEndpointsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminGetEndpointsQuery)
@JwtAuth.permissions_authorized()
async def admin_get_endpoints(request: Request, query: serializers.AdminGetEndpointsQuery):
    
    endpoints_model = serializers.EndpointsModel.model_validate(query, from_attributes=True)
    endpoints_model = endpoints_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if endpoints_model:
        paginator = Paginator(Endpoint.filter(**endpoints_model), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(Endpoint.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    
    results = []
    for item in paginator.items:
        result = serializers.EndpointsModel.model_validate(item, from_attributes=True)
        permissions = [serializers.PermissionsModel.model_validate(item, from_attributes=True) for item in await item.permissions]
        result.permissions = permissions
        results.append(result)

    response = serializers.AdminGetEndpointsSuccessfullyResponse(result=results, total_items=paginator.total_items, total_pages=paginator.total_pages).model_dump()

    return http_response(status = 200, **response)



@AdminBlueprint.post("/endpoints/permissions")
@openapi.summary("endpoints")
@openapi.description("endpoints")
@openapi.secured("token")
@openapi.parameter(name="id", required=False, schema={"id": "int"})
@openapi.parameter(name="endpoint", required=False, schema={"endpoint": "str"})
@openapi.parameter(name="page", required=False, schema={"page": "int"})
@openapi.parameter(name="page_size", required=False, schema={"page_size": "int"})
@openapi.response(status=200, content={"application/json": serializers.AdminPostEndpointsPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminPostEndpointsPermissionsBody)
@JwtAuth.permissions_authorized()
async def admin_post_endpoints_permissions(request: Request, body: serializers.AdminPostEndpointsPermissionsBody):
    if body.id and body.endpoint:
        endpoints_model = Endpoint.filter(id=body.id, role_name=body.endpoint)
    elif body.id:
        endpoints_model = Endpoint.filter(id=body.id)
    elif body.endpoint:
        endpoints_model = Endpoint.filter(role_name=body.endpoint)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await endpoints_model.exists():
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
    
    endpoints_model = await endpoints_model.first()
    permissions_model = await permissions_model.first()

    if permissions_model in await endpoints_model.permissions:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await endpoints_model.permissions.add(permissions_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Endpoint [{endpoints_model.endpoint}] add permission [{permissions_model.permission_title}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Role [{endpoints_model.endpoint}] add permission [{permissions_model.permission_title}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()

    response = serializers.AdminPostEndpointsPermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)



@AdminBlueprint.delete("/endpoints/permissions")
@openapi.summary("endpoints")
@openapi.description("endpoints")
@openapi.secured("token")
@openapi.response(status=204, content={"application/json": serializers.AdminDeleteEndpointsPermissionsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Role is exist")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminDeleteEndpointsPermissionsSuccessfullyResponse)
@JwtAuth.permissions_authorized()
async def admin_delete_endpoints_permissions(request: Request, body: serializers.AdminDeleteEndpointsPermissionsBody):
    if body.id and body.endpoint:
        endpoints_model = Endpoint.filter(id=body.id, role_name=body.endpoint)
    elif body.id:
        endpoints_model = Endpoint.filter(id=body.id)
    elif body.endpoint:
        endpoints_model = Endpoint.filter(role_name=body.endpoint)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await endpoints_model.exists():
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
    
    endpoints_model = await endpoints_model.first()
    permissions_model = await permissions_model.first()

    if permissions_model in await endpoints_model.permissions:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await endpoints_model.permissions.remove(permissions_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Endpoint [{endpoints_model.endpoint}] remove permission [{permissions_model.permission_title}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Endpoint [{endpoints_model.endpoint}] remove permission [{permissions_model.permission_title}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()

    response = serializers.AdminDeleteEndpointsPermissionsSuccessfullyResponse().model_dump()
    return http_response(status = 204, **response)