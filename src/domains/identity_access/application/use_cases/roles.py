from ..contracts import CreateRoleCommand, RolePermissionBinding, UpdateRoleCommand
from ..ports import AuditLogWriter, PermissionRepositoryPort, RoleRepositoryPort
from ...domain import RequestMeta, RoleListQuery, RoleReference
from ...domain.policies import ensure_exists, ensure_not_exists, ensure_relation_absent, ensure_relation_present
from ._audit import record_action


class RoleAdminService:
    def __init__(self, *, roles: RoleRepositoryPort, permissions: PermissionRepositoryPort, audit_logger: AuditLogWriter):
        self.roles = roles
        self.permissions = permissions
        self.audit_logger = audit_logger

    async def list_roles(self, query: RoleListQuery):
        return await self.roles.list(query)

    async def create_role(self, command: CreateRoleCommand, actor_user_id: int, request_meta: RequestMeta):
        ensure_not_exists(await self.roles.exists_by_name(command.role_name), "role already exists")
        role = await self.roles.create(command.role_name)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"New role [{command.role_name}] is created")
        return role

    async def delete_role(self, role_ref: RoleReference, actor_user_id: int, request_meta: RequestMeta):
        filters = role_ref.as_filters()
        ensure_exists(filters, "role filter required")
        role = await self.roles.find(role_ref)
        ensure_exists(role, "role not found")
        await self.roles.delete(role_ref)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"Role [{filters}] is deleted")

    async def update_role(self, command: UpdateRoleCommand, actor_user_id: int, request_meta: RequestMeta):
        role = await self.roles.find(RoleReference(role_id=command.role_id))
        ensure_exists(role, "role not found")
        old_role_name = role.role_name
        role = await self.roles.update(command.role_id, role_name=command.role_name)
        await record_action(
            self.audit_logger,
            actor_user_id,
            request_meta,
            f"Role [{old_role_name}] is renamed to [{command.role_name}]",
        )
        return role

    async def add_permission(self, binding: RolePermissionBinding, actor_user_id: int, request_meta: RequestMeta):
        role = await self.roles.find(binding.role)
        ensure_exists(role, "role not found")
        permission = await self.permissions.find(binding.permission)
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

    async def remove_permission(self, binding: RolePermissionBinding, actor_user_id: int, request_meta: RequestMeta):
        role = await self.roles.find(binding.role)
        ensure_exists(role, "role not found")
        permission = await self.permissions.find(binding.permission)
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
