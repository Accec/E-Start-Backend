from jwt import PyJWT
from functools import wraps

import datetime

from utils.response import AuthorizedError, TokenError
from utils.util import http_response

import asyncio


class JwtAuth:
    _instance = None

    def __new__(cls, secret_key):
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

        encoded_jwt = PyJWT.encode(payload, self.secret_key, algorithm='HS256')
        return encoded_jwt

    def decode_jwt(self, token):
        try:
            decode_jwt = PyJWT.decode(token.encode(), self.secret_key, algorithms=['HS256'])
            return decode_jwt
        except:
            return False

    def authorized(self):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):
                jwt_token = request.token
                is_authorized = self.decode_jwt(jwt_token)

                if is_authorized:
                    request.ctx.user = is_authorized
                    # 如果提供了permissions参数并且用户存在
                    user = kwargs.setdefault(user, None)
                    permissions = kwargs.setdefault(permissions, None)
                    if user and permissions:
                        user = kwargs['user']
                        user_roles = await user.roles.all()
                        # 检查用户是否具有所有必需的权限
                        results = await asyncio.gather(*[
                            role.permissions.filter(permission=permission).exists() for role in user_roles for permission in permissions
                        ])
                        if not all(results):
                            return http_response(AuthorizedError.code, AuthorizedError.msg)
                    
                    response = await f(request, *args, **kwargs)
                    return response
                else:
                    return http_response(TokenError.code, TokenError.msg)
            return decorated_function
        return decorator
