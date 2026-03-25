from functools import lru_cache, wraps

from core.config import load_config
from core.constants import REQUEST_RATE_LIMIT
from core.http import http_response
from core.responses import TooManyRequestsError
from infra.redis import RedisClient


@lru_cache(maxsize=1)
def get_rate_limit_redis():
    config = load_config()
    return RedisClient(config.redis_url)


class RateLimiter:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client

    def _client(self):
        return self.redis_client or get_rate_limit_redis()

    def limit(self, requests=10, seconds=60):
        def decorator(function):
            @wraps(function)
            async def decorated_function(request, *args, **kwargs):
                key = REQUEST_RATE_LIMIT.format(request.ctx.request_path, request.ctx.real_ip)
                count = await self._client().incr(key)

                if count == 1:
                    await self._client().expire(key, seconds)

                if count > requests:
                    return http_response(TooManyRequestsError.code, TooManyRequestsError.msg, status=429)
                return await function(request, *args, **kwargs)

            return decorated_function

        return decorator


def rate_limit(requests=10, seconds=60):
    return RateLimiter().limit(requests=requests, seconds=seconds)
