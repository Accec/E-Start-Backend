from redis import asyncio as aioredis


class RedisClient:
    _instance = None

    def __new__(cls, url) -> aioredis.StrictRedis:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance._init(url)
        return cls._instance
    
    def _init(self, url) -> None:
        connection_pool = aioredis.ConnectionPool.from_url(url, decode_responses=True)
        self.client = aioredis.StrictRedis(connection_pool=connection_pool)
    
    def __getattr__ (self, name) -> aioredis.StrictRedis:
        return getattr(self.client, name)


if __name__ == "__main__":
    import asyncio

    a = RedisClient("redis://localhost:6379/0")
    print(asyncio.run(a.get("bb")))