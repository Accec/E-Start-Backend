from utils.router import UserBlueprint
from utils.util import http_response
from utils.constant import LogLevel, UserStatus
from utils.constant import API_LOGGER

from sanic.request import Request
from sanic_ext import validate

from . import serializers

import logging

import config
from models import User, Log

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

Config = config.Config()
JwtAuth = jwt.JwtAuth()
Logger = logging.getLogger(API_LOGGER)

@UserBlueprint.post("/login")
@rate_limit(5, 60)
@validate(json=serializers.UserPostLoginBody)
async def user_post_login(request: Request, body: serializers.UserPostLoginBody):
    user = await User.get_or_none(account=body.account)
    if not user:
        response = serializers.AccountOrPasswordInvalidResponse().model_dump()
        return http_response(status = 401, **response)
        
    log = Log(user = user, api = request.uri_template, ip = request.ctx.real_ip, ua = request.ctx.ua)

    password = hash_password(body.password)
    if password != user.password:
        log.action = "Login failed!"
        log.level = LogLevel.MIDIUM
        await log.save()
        response = serializers.AccountOrPasswordInvalidResponse().model_dump()
        return http_response(status = 401, **response)
    
    if user.status == UserStatus.INACTIVE:
        log.action = "Ban"
        log.level = LogLevel.MIDIUM
        await log.save()
        response = serializers.AccountOrPasswordInvalidResponse().model_dump()
        return http_response(status = 401, **response)
    
    log.action = "Login successfully!"
    log.level = LogLevel.MIDIUM
    await log.save()
    
    token = JwtAuth.encode_jwt(user.id, Config.JwtExpTime)

    response = serializers.UserPostLoginSuccessfullyResponse(token = token).model_dump()
    return http_response(status=200, **response)