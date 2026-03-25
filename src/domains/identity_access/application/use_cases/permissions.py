from ..contracts import CreatePermissionCommand, UpdatePermissionCommand
from ..ports import AuditLogWriter, PermissionRepositoryPort
from ...domain import PermissionListQuery, PermissionReference, RequestMeta
from ...domain.policies import ensure_exists, ensure_not_exists
from ._audit import record_action


class PermissionAdminService:
    def __init__(self, *, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_permissions(self, query: PermissionListQuery):
        return await self.permissions.list(query)

    async def create_permission(self, command: CreatePermissionCommand, actor_user_id: int, request_meta: RequestMeta):
        ensure_not_exists(await self.permissions.exists_by_title(command.permission_title), "permission already exists")
        permission = await self.permissions.create(command.permission_title)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"New permission [{command.permission_title}] is created",
        )
        return permission

    async def delete_permission(self, permission_ref: PermissionReference, actor_user_id: int, request_meta: RequestMeta):
        filters = permission_ref.as_filters()
        ensure_exists(filters, "permission filter required")
        permission = await self.permissions.find(permission_ref)
        ensure_exists(permission, "permission not found")
        await self.permissions.delete(permission_ref)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"Permission [{filters}] is deleted")

    async def update_permission(self, command: UpdatePermissionCommand, actor_user_id: int, request_meta: RequestMeta):
        permission = await self.permissions.find(PermissionReference(permission_id=command.permission_id))
        ensure_exists(permission, "permission not found")
        old_permission_title = permission.permission_title
        permission = await self.permissions.update(command.permission_id, permission_title=command.permission_title)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Permission [{old_permission_title}] is renamed to [{command.permission_title}]",
        )
        return permission
