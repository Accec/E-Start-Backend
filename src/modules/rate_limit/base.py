from functools import wraps
from sanic.response import json
from sanic.exceptions import abort

async def get_redis_pool():
    # Update this with your Redis connection details
    return await aioredis.create_redis_pool('redis://localhost')

def rate_limit(requests=10, seconds=60):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            redis = await get_redis_pool()
            ip = request.ip
            key = f"ratelimit:{ip}"
            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, seconds)
                if count > requests:
                    abort(429, "Too many requests")
                response = await f(request, *args, **kwargs)
                return response
            finally:
                redis.close()
        return decorated_function
    return decorator
