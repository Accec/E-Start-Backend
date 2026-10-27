from ..ports import AuditLogWriter, PermissionRepositoryPort
from ..audit import RequestMeta, record_action
from ..policies import ensure_exists, ensure_not_exists


class PermissionAdminService:
    def __init__(self, *, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_permissions(
        self, *, permission_id: int | None = None, permission_title: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        return await self.permissions.list(
            permission_id=permission_id, permission_title=permission_title, page=page, page_size=page_size,
        )

    async def create_permission(self, *, permission_title: str | None, actor_user_id: int, request_meta: RequestMeta):
        ensure_not_exists(await self.permissions.exists_by_title(permission_title), "permission already exists")
        permission = await self.permissions.create(permission_title)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"New permission [{permission_title}] is created",
        )
        return permission

    async def delete_permission(
        self, *, permission_id: int | None = None, permission_title: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        filters = {
            key: value
            for key, value in {"id": permission_id, "permission_title": permission_title}.items()
            if value is not None
        }
        ensure_exists(filters, "permission filter required")
        permission = await self.permissions.find(permission_id=permission_id, permission_title=permission_title)
        ensure_exists(permission, "permission not found")
        await self.permissions.delete(permission_id=permission_id, permission_title=permission_title)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"Permission [{filters}] is deleted")

    async def update_permission(
        self, *, permission_id: int | None, permission_title: str | None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        permission = await self.permissions.find(permission_id=permission_id)
        ensure_exists(permission, "permission not found")
        old_permission_title = permission.permission_title
        permission = await self.permissions.update(permission_id, permission_title=permission_title)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Permission [{old_permission_title}] is renamed to [{permission_title}]",
        )
        return permission
