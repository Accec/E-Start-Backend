from ..ports import AuditLogWriter, EndpointRepositoryPort, PermissionRepositoryPort
from ..audit import RequestMeta, record_action
from ..policies import ensure_exists, ensure_relation_absent, ensure_relation_present


class EndpointAdminService:
    def __init__(self, *, endpoints: EndpointRepositoryPort, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.endpoints = endpoints
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_endpoints(
        self, *, endpoint_id: int | None = None, endpoint_path: str | None = None, method: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        return await self.endpoints.list(
            endpoint_id=endpoint_id, endpoint_path=endpoint_path, method=method, page=page, page_size=page_size,
        )

    async def add_permission(
        self, *, endpoint_id: int | None = None, endpoint_path: str | None = None, method: str | None = None,
        permission_id: int | None = None, permission_title: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        endpoint = await self.endpoints.find(endpoint_id=endpoint_id, endpoint_path=endpoint_path, method=method)
        ensure_exists(endpoint, "endpoint not found")
        permission = await self.permissions.find(permission_id=permission_id, permission_title=permission_title)
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

    async def remove_permission(
        self, *, endpoint_id: int | None = None, endpoint_path: str | None = None, method: str | None = None,
        permission_id: int | None = None, permission_title: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        endpoint = await self.endpoints.find(endpoint_id=endpoint_id, endpoint_path=endpoint_path, method=method)
        ensure_exists(endpoint, "endpoint not found")
        permission = await self.permissions.find(permission_id=permission_id, permission_title=permission_title)
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
