import json

from core.constants import ENDPOINT_PERMISSIONS_KEY, USER_PERMISSIONS_KEY
from infra.redis import RedisClient


class RedisAuthorizationCache:
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client

    def _normalize_endpoint(self, endpoint: str):
        return endpoint[1:] if endpoint.startswith("/") else endpoint

    async def get_endpoint_permissions(self, method: str, endpoint: str):
        key = ENDPOINT_PERMISSIONS_KEY.format(method, self._normalize_endpoint(endpoint))
        payload = await self.redis_client.get(key)
        if payload is None:
            return None
        return set(json.loads(payload))

    async def set_endpoint_permissions(self, method: str, endpoint: str, permissions: set[str], ttl_seconds: int):
        key = ENDPOINT_PERMISSIONS_KEY.format(method, self._normalize_endpoint(endpoint))
        await self.redis_client.set(key, json.dumps(sorted(permissions)), ex=ttl_seconds)

    async def get_user_permissions(self, user_id: int):
        key = USER_PERMISSIONS_KEY.format(user_id)
        payload = await self.redis_client.get(key)
        if payload is None:
            return None
        return set(json.loads(payload))

    async def set_user_permissions(self, user_id: int, permissions: set[str], ttl_seconds: int):
        key = USER_PERMISSIONS_KEY.format(user_id)
        await self.redis_client.set(key, json.dumps(sorted(permissions)), ex=ttl_seconds)
