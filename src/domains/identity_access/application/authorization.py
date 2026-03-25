from core.constants import LogLevel, UserStatus
from domains.audit.domain import AuditLogRecord

from .ports import AuditLogWriter, AuthorizationCache, EndpointRepositoryPort, UserRepositoryPort

class AuthorizationService:
    def __init__(
        self,
        *,
        users: UserRepositoryPort,
        endpoints: EndpointRepositoryPort,
        audit_logger: AuditLogWriter,
        cache: AuthorizationCache | None = None,
        cache_ttl_seconds: int = 30,
    ):
        self.users = users
        self.endpoints = endpoints
        self.audit_logger = audit_logger
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_endpoint_permissions(self, method: str, endpoint: str):
        cached_permissions = None
        if self.cache is not None:
            cached_permissions = await self.cache.get_endpoint_permissions(method, endpoint)
        if cached_permissions is not None:
            return cached_permissions

        normalized_endpoint = endpoint[1:] if endpoint.startswith("/") else endpoint
        permissions = await self.endpoints.get_permission_titles(method, normalized_endpoint)
        if permissions and self.cache is not None:
            await self.cache.set_endpoint_permissions(method, endpoint, permissions, ttl_seconds=self.cache_ttl_seconds)
        return permissions

    async def get_user_permissions(self, user_id: int):
        cached_permissions = None
        if self.cache is not None:
            cached_permissions = await self.cache.get_user_permissions(user_id)
        if cached_permissions is not None:
            return cached_permissions

        user = await self.users.get_by_id(user_id)
        if not user:
            return False
        if user.status == UserStatus.INACTIVE:
            return False

        permissions = await self.users.get_permission_titles(user_id)
        if permissions and self.cache is not None:
            await self.cache.set_user_permissions(user_id, permissions, ttl_seconds=self.cache_ttl_seconds)
        return permissions

    async def authorize(self, user_id: int, method: str, endpoint: str, ip: str, ua: str):
        endpoint_permissions = await self.get_endpoint_permissions(method, endpoint)
        if not endpoint_permissions:
            return True

        user_permissions = await self.get_user_permissions(user_id)
        if user_permissions is False or not all(permission in user_permissions for permission in endpoint_permissions):
            await self.audit_logger.record(
                AuditLogRecord(
                    user_id=user_id,
                    api=endpoint,
                    action="Privilege escalation",
                    ip=ip,
                    ua=ua,
                    level=LogLevel.HIGH,
                )
            )
            return False
        return True
