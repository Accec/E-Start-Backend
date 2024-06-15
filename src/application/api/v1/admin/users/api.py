from utils.router import AdminBlueprint
from utils.util import http_response, Paginator

from utils.constant import API_LOGGER
from utils.constant import LogLevel

from sanic.request import Request
from sanic_ext import validate

from . import serializers
from models import User, Log, Role

from modules.encryptor import hash_password, generate_openid
from modules.auth import jwt

import datetime
import logging


Logger = logging.getLogger(API_LOGGER)
JwtAuth = jwt.JwtAuth()

@AdminBlueprint.get("/users")
@validate(query=serializers.AdminGetUsersQuery)
@JwtAuth.permissions_authorized()
async def admin_get_users(request: Request, query: serializers.AdminGetUsersQuery):
    
    users_model = serializers.UsersModel.model_validate(query, from_attributes=True)
    users_model = users_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if users_model:
        paginator = Paginator(User.filter(**users_model), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(User.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    
    results = []
    for item in paginator.items:
        result = serializers.UsersModel.model_validate(item, from_attributes=True)
        roles = [serializers.RolesModel.model_validate(item, from_attributes=True) for item in await item.roles]
        result.roles = roles
        results.append(result)

    response = serializers.AdminGetUsersSuccessfullyResponse(result=results, total_items=paginator.total_items, total_pages=paginator.total_pages).model_dump()

    return http_response(status = 200, **response)



@AdminBlueprint.post("/users")
@validate(json=serializers.AdminPostUsersBody)
@JwtAuth.permissions_authorized()
async def admin_post_users(request: Request, body: serializers.AdminPostUsersBody):
    if await User.exists(account=body.account):
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status=400, **response)
    
    open_id = generate_openid(body.account, str(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
    hashed_password = hash_password(body.password) 
    
    new_user = User(account=body.account, password=hashed_password, open_id = open_id)
    await new_user.save()
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - New User [{body.account}] is created")
    new_log = Log(user = user, api = request.uri_template, action = f"New User [{body.account}] is created", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPostUsersSuccessfullyResponse().model_dump()
    return http_response(status=201, **response)



@AdminBlueprint.put("/users")
@validate(json=serializers.AdminPutUsersBody)
@JwtAuth.permissions_authorized()
async def admin_put_users(request: Request, body: serializers.AdminPutUsersBody):
    user_model = User.filter(id = body.id)
    if not await user_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    old_user_model = user_model

    await user_model.update(**body)
    # create log
    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - Users [{await old_user_model.values()}] is change to [{await user_model.values()}]")
    new_log = Log(user = user, api = request.uri_template, action = f"Users [{await old_user_model.values()}] is change to [{await user_model.values()}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPutUsersSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)



@AdminBlueprint.post("/users/roles")
@validate(query=serializers.AdminPostUsersRolesBody)
@JwtAuth.permissions_authorized()
async def admin_post_users_roles(request: Request, body: serializers.AdminPostUsersRolesBody):
    if body.id and body.account:
        users_model = User.filter(id=body.id, role_name=body.account)
    elif body.id:
        users_model = User.filter(id=body.id)
    elif body.account:
        users_model = User.filter(role_name=body.account)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await users_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)

    roles_model = serializers.RolesModel.model_validate(body.roles, from_attributes=True)
    roles_model = roles_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if roles_model:
        roles_model = Role.filter(**roles_model)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    users_model = await users_model.first()
    roles_model = await roles_model.first()

    if roles_model in await users_model.roles:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await users_model.roles.add(roles_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - User [{users_model.account}] add Role [{roles_model.role_name}]")
    new_log = Log(user = user, api = request.uri_template, action = f"User [{users_model.account}] add Role [{roles_model.role_name}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminPostUsersRolesSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)



@AdminBlueprint.delete("/users/roles")
@validate(json=serializers.AdminDeleteUsersRolesBody)
@JwtAuth.permissions_authorized()
async def admin_delete_users_roles(request: Request, body: serializers.AdminDeleteUsersRolesBody):
    if body.id and body.account:
        users_model = User.filter(id=body.id, role_name=body.account)
    elif body.id:
        users_model = User.filter(id=body.id)
    elif body.account:
        users_model = User.filter(role_name=body.account)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await users_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)

    roles_model = serializers.RolesModel.model_validate(body.roles, from_attributes=True)
    roles_model = roles_model.model_dump(exclude_none = True, exclude_defaults = True, exclude_unset=True)
    if roles_model:
        roles_model = Role.filter(**roles_model)
    else:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await roles_model.exists():
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    users_model = await users_model.first()
    roles_model = await roles_model.first()

    if roles_model in await users_model.roles:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    await users_model.roles.remove(roles_model)

    user_id = request.ctx.user['user_id']
    user = await User.get(id=user_id)
    Logger.info(f"[Admin] - User [{users_model.account}] remove Role [{roles_model.role_name}]")
    new_log = Log(user = user, api = request.uri_template, action = f"User [{users_model.account}] remove Role [{roles_model.role_name}]", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.AdminDeleteUsersRolesSuccessfullyResponse().model_dump()
    return http_response(status = 204, **response)