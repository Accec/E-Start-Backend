import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

try:
    from redis import asyncio as aioredis
except ModuleNotFoundError:
    aioredis = None


logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, url) -> None:
        if aioredis is None:
            raise ModuleNotFoundError("redis package is required to use RedisClient")
        self.url = url
        connection_pool = aioredis.ConnectionPool.from_url(url, decode_responses=True)
        self.client = aioredis.StrictRedis(connection_pool=connection_pool)

    def __getattr__(self, name) -> Any:
        return getattr(self.client, name)

    def locker(self, lock_key="default"):
        return RedisLock(self, lock_key)


class RedisLock:
    def __init__(self, redis_client, lock_key):
        self.client = redis_client
        self.lock_key = f"lock:{lock_key}"
        self.identifier = str(uuid.uuid4())

    async def _acquire_lock(self, acquire_timeout=60, lock_timeout=60):
        end = time.time() + acquire_timeout
        while time.time() < end:
            if await self.client.set(self.lock_key, self.identifier, ex=lock_timeout, nx=True):
                return True
            await asyncio.sleep(0.3)
        return False

    async def _release_lock(self):
        try:
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.client.eval(script, 1, self.lock_key, self.identifier)
        except Exception:
            logger.exception("Failed to release redis lock %s", self.lock_key)

    @asynccontextmanager
    async def lock(self, acquire_timeout=60, lock_timeout=60):
        acquired = await self._acquire_lock(acquire_timeout, lock_timeout)
        try:
            if acquired:
                yield
            else:
                raise RuntimeError(f"Failed to acquire redis lock {self.lock_key}")
        finally:
            if acquired:
                await self._release_lock()
