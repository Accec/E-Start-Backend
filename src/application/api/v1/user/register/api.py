from utils.response import Successfully, RequestError, UserExistError
from utils.constant import LOG_LEVEL_MIDIUM, ROLE_USER
from utils.router import UserBlueprint
from utils.util import http_response
from sanic_ext import validate, openapi

from sanic.request import Request

import datetime

from . import serializers
from models import User, Log, Role
from modules.rate_limit import rate_limit
from modules.encryptor import hash_password, generate_openid


@UserBlueprint.post("/register")
@openapi.summary("Register")
@openapi.description("Register")
@openapi.body({"application/json": serializers.RegisterPayloads.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=500, content={"ArgsInvalidResponse": serializers.ArgsInvalidResponse.model_json_schema(), "UserExistResponse": serializers.UserExistResponse.model_json_schema()}, description="Args invalid | The account is exist")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@rate_limit(5, 60)
@validate(json=serializers.RegisterPayloads)
async def post_register(request: Request, body: serializers.RegisterPayloads):
    if await User.exists(account=body.account):
        return http_response(UserExistError.code, UserExistError.msg, status=500)

    # generate open id and hash password
    open_id = generate_openid(body.account, body.password, str(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
    hashed_password = hash_password(body.password)
    # save user
    new_user = User(account=body.account, password=hashed_password, open_id = open_id)
    await new_user.save()
    # create the association between the user and the role
    role = await Role.get(id=ROLE_USER)
    await new_user.roles.add(role)
    # create log
    new_log = Log(user = new_user, api = request.uri_template, action = "Register successfully!", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_MIDIUM)
    await new_log.save()
    return http_response(Successfully.code, Successfully.msg, status=201)