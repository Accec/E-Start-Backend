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
@openapi.summary("User Login")
@openapi.description("Allows users to authenticate by providing account credentials. Returns a JWT token upon successful authentication.")
@openapi.body({"application/json": serializers.PostLoginBody.model_json_schema()})
@openapi.response(status=200, content={"application/json": serializers.SuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.AccountOrPasswordInvalidResponse.model_json_schema()}, description="Account or password_invalid")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@rate_limit(5, 60)
@validate(json=serializers.PostLoginBody)
async def user_post_login(request: Request, body: serializers.PostLoginBody):
    user = await User.get_or_none(account=body.account)
    if not user:
        return http_response(AccountOrPasswordInvalid.code, AccountOrPasswordInvalid.msg, status=401)
    
    log = Log(user = user, api = request.uri_template, ip = request.ctx.real_ip, ua = request.ctx.ua)

    password = hash_password(body.password)
    if password != user.password:
        log.action = "Login failed!"
        log.level = LOG_LEVEL_MIDIUM
        await log.save()
        return http_response(AccountOrPasswordInvalid.code, AccountOrPasswordInvalid.msg, status=401)
    
    log.action = "Login successfully!"
    log.level = LOG_LEVEL_MIDIUM
    await log.save()
    
    token = JwtAuth.encode_jwt(user.id, Config.JwtExpTime)
    return http_response(Successfully.code, Successfully.msg, token = token, status=200)