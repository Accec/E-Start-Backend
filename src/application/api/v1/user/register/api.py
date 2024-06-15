from utils.constant import LogLevel
from utils.constant import ROLE_USER
from utils.constant import API_LOGGER
from utils.router import UserBlueprint
from utils.util import http_response
from sanic_ext import validate, openapi

from sanic.request import Request

import datetime

from . import serializers
from models import User, Log, Role
from modules.rate_limit import rate_limit
from modules.encryptor import hash_password, generate_openid

import logging


Logger = logging.getLogger(API_LOGGER)

@UserBlueprint.post("/register")
@openapi.summary("Register")
@openapi.description("Register")
@openapi.body({"application/json": serializers.UserPostRegisterBody.model_json_schema()})
@openapi.response(status=201, content={"application/json": serializers.UserPostLoginSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"ArgsInvalidResponse": serializers.ArgsInvalidResponse.model_json_schema(), "UserExistResponse": serializers.UserExistResponse.model_json_schema()}, description="Args invalid | The account is exist")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@rate_limit(5, 60)
@validate(json=serializers.UserPostRegisterBody)
async def user_post_register(request: Request, body: serializers.UserPostRegisterBody):
    if await User.exists(account=body.account):
        response = serializers.UserExistResponse().model_dump()
        return http_response(status = 400, **response)

    # generate open id and hash password
    open_id = generate_openid(body.account, str(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
    hashed_password = hash_password(body.password)
    # save user
    new_user = User(account=body.account, password=hashed_password, open_id = open_id)
    await new_user.save()
    # create the association between the user and the role
    role = await Role.get(role_name=ROLE_USER)
    await new_user.roles.add(role)
    # create log
    Logger.info(f"[User] - [{body.account}] Register")
    new_log = Log(user = new_user, api = request.uri_template, action = "Register successfully!", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LogLevel.MIDIUM)
    await new_log.save()

    response = serializers.UserPostLoginSuccessfullyResponse().model_dump()
    return http_response(status=201, **response)