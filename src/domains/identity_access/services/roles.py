from ..ports import AuditLogWriter, PermissionRepositoryPort, RoleRepositoryPort
from ..audit import RequestMeta, record_action
from ..policies import ensure_exists, ensure_not_exists, ensure_relation_absent, ensure_relation_present


class RoleAdminService:
    def __init__(self, *, roles: RoleRepositoryPort, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.roles = roles
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_roles(
        self, *, role_id: int | None = None, role_name: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        return await self.roles.list(role_id=role_id, role_name=role_name, page=page, page_size=page_size)

    async def create_role(self, *, role_name: str | None, actor_user_id: int, request_meta: RequestMeta):
        ensure_not_exists(await self.roles.exists_by_name(role_name), "role already exists")
        role = await self.roles.create(role_name)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"New role [{role_name}] is created")
        return role

    async def delete_role(
        self, *, role_id: int | None = None, role_name: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        filters = {key: value for key, value in {"id": role_id, "role_name": role_name}.items() if value is not None}
        ensure_exists(filters, "role filter required")
        role = await self.roles.find(role_id=role_id, role_name=role_name)
        ensure_exists(role, "role not found")
        await self.roles.delete(role_id=role_id, role_name=role_name)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"Role [{filters}] is deleted")

    async def update_role(
        self, *, role_id: int | None, role_name: str | None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        role = await self.roles.find(role_id=role_id)
        ensure_exists(role, "role not found")
        old_role_name = role.role_name
        role = await self.roles.update(role_id, role_name=role_name)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Role [{old_role_name}] is renamed to [{role_name}]",
        )
        return role

    async def add_permission(
        self, *, role_id: int | None = None, role_name: str | None = None,
        permission_id: int | None = None, permission_title: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        role = await self.roles.find(role_id=role_id, role_name=role_name)
        ensure_exists(role, "role not found")
        permission = await self.permissions.find(permission_id=permission_id, permission_title=permission_title)
        ensure_exists(permission, "permission not found")
        ensure_relation_absent(await self.roles.has_permission(role, permission), "permission already assigned")
        await self.roles.add_permission(role, permission)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Role [{role.role_name}] add permission [{permission.permission_title}]",
        )
        return role, permission

    async def remove_permission(
        self, *, role_id: int | None = None, role_name: str | None = None,
        permission_id: int | None = None, permission_title: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        role = await self.roles.find(role_id=role_id, role_name=role_name)
        ensure_exists(role, "role not found")
        permission = await self.permissions.find(permission_id=permission_id, permission_title=permission_title)
        ensure_exists(permission, "permission not found")
        ensure_relation_present(await self.roles.has_permission(role, permission), "permission not assigned")
        await self.roles.remove_permission(role, permission)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Role [{role.role_name}] remove permission [{permission.permission_title}]",
        )
        return role, permission
