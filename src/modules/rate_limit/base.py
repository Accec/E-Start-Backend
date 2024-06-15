from functools import wraps

import config
from utils import redis_conn
from utils.constant import REQUEST_RATE_LIMIT
from utils.response import RateLimitError
from utils.util import http_response


Config = config.Config()
RedisConn = redis_conn.RedisClient(Config.RedisUrl)

def rate_limit(requests=10, seconds=60):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            key = REQUEST_RATE_LIMIT.format(request.uri_template, request.ctx.real_ip)
            count = await RedisConn.incr(key)

            if count >= 1:
                await RedisConn.expire(key, seconds)
                
            if count > requests:
                return http_response(429, "Too many requests")
            response = await f(request, *args, **kwargs)
            return response
        return decorated_function
    return decorator
