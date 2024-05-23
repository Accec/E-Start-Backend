from jwt import PyJWT
from functools import wraps

import datetime

from utils.constant import LOG_LEVEL_HIGH, USER_PERMISSIONS_KEY, ENDPOINT_PERMISSIONS_KEY
from utils.response import AuthorizedError, TokenError
from utils.util import http_response

import config
from utils import redis_conn
from models import User, Permission, Log, Endpoint

import ujson
import asyncio

Config = config.Config()
RedisConn = redis_conn.RedisClient(Config.RedisUrl)

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
        
    async def get_endpoint_permissions(self, endpoint):
        permissions_key = ENDPOINT_PERMISSIONS_KEY.format(endpoint)
        permissions = await RedisConn.get(permissions_key)
        if permissions is not None:
            return set(ujson.loads(permissions))

        # 如果缓存中没有，从数据库查询
        endpoint = await Endpoint.get(endpoint=endpoint)
        permissions = await endpoint.permissions.all()

        endpoint_permissions = [permission.permission_title for permission in permissions]
        # 将结果缓存，设置过期时间为1小时
        await RedisConn.set(permissions_key, ujson.dumps(endpoint_permissions), expire=3600)

        return endpoint_permissions
        
    async def get_user_permissions(self, user_id):
        permissions_key = USER_PERMISSIONS_KEY.format(user_id)
        permissions = await RedisConn.get(permissions_key)
        if permissions is not None:
            return set(ujson.loads(permissions))

        # 如果缓存中没有，从数据库查询
        user = await User.get(id=user_id).prefetch_related("roles")
        roles = await user.roles.all()

        role_permissions = await asyncio.gather(*(role.permissions.all() for role in roles))
        user_permissions = {perm.permission_title for perms in role_permissions for perm in perms}

        # 将结果缓存，设置过期时间为1小时
        await RedisConn.set(permissions_key, ujson.dumps(list(user_permissions)), expire=3600)

        return user_permissions

    def permissions_authorized(self):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):
                jwt_token = request.token
                endpoint = request.uri_template
                is_authorized = self.decode_jwt(jwt_token)

                if is_authorized:
                    permissions = self.get_endpoint_permissions(endpoint)
                    request.ctx.user = is_authorized
                    if permissions:
                        user_id = request.ctx.user['user_id']
                        user_permissions = await self.get_user_permissions(user_id)
                        # 检查用户是否拥有所需的所有权限
                        if not all(perm in user_permissions for perm in permissions):
                            new_log = Log(user = user_id, api = request.uri_template, action = "Privilege escalation", ip = request.ctx.real_ip, ua = request.ctx.ua, level = LOG_LEVEL_HIGH)
                            await new_log.save()
                            return http_response(AuthorizedError.code, AuthorizedError.msg, status=403)
                                            
                    response = await f(request, *args, **kwargs)
                    return response
                else:
                    return http_response(TokenError.code, TokenError.msg, status=401)
            return decorated_function
        return decorator