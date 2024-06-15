from redis import asyncio as aioredis
from contextlib import asynccontextmanager
import time
import uuid
import asyncio


class RedisClient:
    _instance = None

    def __new__(cls, url) -> aioredis.StrictRedis:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance._init(url)
        return cls._instance
    
    def _init(self, url) -> aioredis.StrictRedis:
        connection_pool = aioredis.ConnectionPool.from_url(url, decode_responses=True)
        self.client = aioredis.StrictRedis(connection_pool=connection_pool)
        
    
    def __getattr__ (self, name) -> aioredis.StrictRedis:
        return getattr(self.client, name)
    
    def locker(self, lock_key="default"):
        return RedisLock(self, lock_key)
    
class RedisLock:
    def __init__(self, redis_client, lock_key):
        self.client = redis_client
        self.lock_key = f"lock:{lock_key}"
        self.identifier = uuid.uuid1().__str__()  # uuid1 to uuid4 for better randomness
    
    async def _acquire_lock(self, acquire_timeout=60, lock_timeout=60):
        end = time.time() + acquire_timeout
        while time.time() < end:
            if await self.client.set(self.lock_key, self.identifier, ex=lock_timeout, nx=True):
                return True
            await asyncio.sleep(0.3)  # Adjusted sleep time if needed
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
        except Exception as e:
            print(f"Failed to release lock: {str(e)}")  # Log error or handle it appropriately
    
    @asynccontextmanager
    async def lock(self, acquire_timeout=60, lock_timeout=60):
        acquired = await self._acquire_lock(acquire_timeout, lock_timeout)
        try:
            if acquired:
                yield
            else:
                raise Exception("Failed to acquire lock")
        finally:
            if acquired:
                await self._release_lock()

    


if __name__ == "__main__":
    import asyncio

    a = RedisClient("redis://localhost:6379/0")
    print(asyncio.run(a.get("bb")))