from utils.router import UserBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError, AccountOrPasswordInvalid
from utils.constant import LOG_LEVEL_HIGH, LOG_LEVEL_MIDIUM

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers

import config
from models import User, Log, Role

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

Config = config.Config()
JwtAuth = jwt.JwtAuth()

@UserBlueprint.post("/login")
@openapi.summary("Login")
@openapi.description("Login")
@openapi.body({"application/json": serializers.LoginPayloads.model_json_schema()})
@openapi.response(status=200, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=500, content={"ArgsInvalidResponse": serializers.ArgsInvalidResponse.model_json_schema(), "AccountOrPasswordInvalidResponse": serializers.AccountOrPasswordInvalidResponse.model_json_schema()}, description="Args invalid | The account or password invalid ")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@rate_limit(5, 60)
@validate(json=serializers.LoginPayloads)
async def post_login(request: Request, body: serializers.LoginPayloads):
    user = await User.get_or_none(account=body.account)
    if not user:
        return http_response(AccountOrPasswordInvalid.code, AccountOrPasswordInvalid.msg, status=500)
    
    log = Log(user = user, api = request.uri_template, ip = request.ctx.real_ip, ua = request.ctx.ua)

    password = hash_password(body.password)
    if password != user.password:
        log.action = "Login failed!"
        log.level = LOG_LEVEL_MIDIUM
        await log.save()
        return http_response(AccountOrPasswordInvalid.code, AccountOrPasswordInvalid.msg, status=500)
    
    log.action = "Login successfully!"
    log.level = LOG_LEVEL_MIDIUM
    await log.save()
    
    token = JwtAuth.encode_jwt(user.id, Config.JwtExpTime)
    return http_response(Successfully.code, Successfully.msg, token = token, status=200)