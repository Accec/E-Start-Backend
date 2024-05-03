from jwt import PyJWT
from functools import wraps

import datetime

from utils.constant import LOG_LEVEL_HIGH
from utils.response import AuthorizedError, TokenError
from utils.util import http_response

from models import User, Permission, Log


import asyncio


class JwtAuth:
    _instance = None

    def __new__(cls, secret_key=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(secret_key)
        return cls._instance
    
    def _init(self, secret_key) -> None:
        self.secret_key = secret_key

    def encode_jwt(self, user_id, exp):
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds = exp)
        }
        
        encoded_jwt = PyJWT().encode(payload, self.secret_key, algorithm='HS256')
        return encoded_jwt

    def decode_jwt(self, token:str):
        try:            
            decode_jwt = PyJWT().decode(token.encode(), self.secret_key, algorithms=['HS256'])
            return decode_jwt
        except Exception as e:
            print (e.__str__())
            return False

    def authorized(self, *permissions):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):
                jwt_token = request.token
                is_authorized = self.decode_jwt(jwt_token)

                if is_authorized:
                    request.ctx.user = is_authorized
                    if permissions:
                        user = await User.get(id=is_authorized["user_id"]).prefetch_related("roles")
                        roles = await user.roles.all()  # 获取关联的角色列表
                        # 获取用户所有角色的权限
                        user_permissions = set()
                        for role in roles:
                            role_permissions = await role.permissions.all()
                            for perm in role_permissions:
                                user_permissions.add(perm.permission_title)

                        # 检查用户是否拥有所需的所有权限
                        if not all(perm in user_permissions for perm in permissions):
                            new_log = Log(user = user, api = request.uri_template, action = "Privilege escalation", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_HIGH)
                            await new_log.save()
                            return http_response(AuthorizedError.code, AuthorizedError.msg, status=401)
                                            
                    response = await f(request, *args, **kwargs)
                    return response
                else:
                    return http_response(TokenError.code, TokenError.msg, status=401)
            return decorated_function
        return decorator
