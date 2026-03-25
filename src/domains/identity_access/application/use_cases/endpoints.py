from ..contracts import EndpointPermissionBinding
from ..ports import AuditLogWriter, EndpointRepositoryPort, PermissionRepositoryPort
from ...domain import EndpointListQuery, RequestMeta
from ...domain.policies import ensure_exists, ensure_relation_absent, ensure_relation_present
from ._audit import record_action


class EndpointAdminService:
    def __init__(self, *, endpoints: EndpointRepositoryPort, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.endpoints = endpoints
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_endpoints(self, query: EndpointListQuery):
        return await self.endpoints.list(query)

    async def add_permission(self, binding: EndpointPermissionBinding, actor_user_id: int, request_meta: RequestMeta):
        endpoint = await self.endpoints.find(binding.endpoint)
        ensure_exists(endpoint, "endpoint not found")
        permission = await self.permissions.find(binding.permission)
        ensure_exists(permission, "permission not found")
        ensure_relation_absent(await self.endpoints.has_permission(endpoint, permission), "permission already assigned")
        await self.endpoints.add_permission(endpoint, permission)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Endpoint [{endpoint.endpoint}] add permission [{permission.permission_title}]",
        )
        return endpoint, permission

    async def remove_permission(self, binding: EndpointPermissionBinding, actor_user_id: int, request_meta: RequestMeta):
        endpoint = await self.endpoints.find(binding.endpoint)
        ensure_exists(endpoint, "endpoint not found")
        permission = await self.permissions.find(binding.permission)
        ensure_exists(permission, "permission not found")
        ensure_relation_present(await self.endpoints.has_permission(endpoint, permission), "permission not assigned")
        await self.endpoints.remove_permission(endpoint, permission)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Endpoint [{endpoint.endpoint}] remove permission [{permission.permission_title}]",
        )
        return endpoint, permission
