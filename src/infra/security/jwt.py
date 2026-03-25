from functools import wraps
import datetime

from jwt import PyJWT

from core.http import http_response
from core.responses import PermissionDeniedError, TokenExpiredError


class JwtAuth:
    def __init__(self, *, secret_key, authorization_service):
        self.secret_key = secret_key
        self.authorization_service = authorization_service

    def encode_jwt(self, user_id, exp):
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=exp),
        }

        encoded_jwt = PyJWT().encode(payload, self.secret_key, algorithm="HS256")
        return encoded_jwt

    def decode_jwt(self, token: str):
        if not token or not self.secret_key:
            return False
        try:
            decode_jwt = PyJWT().decode(token.encode(), self.secret_key, algorithms=["HS256"])
            return decode_jwt
        except Exception:
            return False

    def permissions_authorized(self):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request, *args, **kwargs):
                jwt_token = request.token
                endpoint = request.ctx.request_path
                method = request.method

                decoded_jwt = self.decode_jwt(jwt_token)
                if not decoded_jwt:
                    return http_response(TokenExpiredError.code, TokenExpiredError.msg, status=401)

                request.ctx.user = decoded_jwt
                user_id = int(decoded_jwt["user_id"])
                is_authorized = await self.authorization_service.authorize(
                    user_id=user_id,
                    method=method,
                    endpoint=endpoint,
                    ip=request.ctx.real_ip,
                    ua=request.ctx.ua,
                )
                if not is_authorized:
                    return http_response(PermissionDeniedError.code, PermissionDeniedError.msg, status=403)

                response = await f(request, *args, **kwargs)
                return response

            return decorated_function

        return decorator
