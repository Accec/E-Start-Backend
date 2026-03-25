from core.time import get_timestamp

from ..ports import AuditLogWriter, CredentialService, RoleRepositoryPort, UserRepositoryPort
from ..contracts import CreateUserCommand, UpdateUserCommand, UserRoleBinding
from ...domain import RequestMeta, UserListQuery
from ...domain.policies import ensure_exists, ensure_not_exists, ensure_relation_absent, ensure_relation_present
from ._audit import record_action


class UserAdminService:
    def __init__(
        self,
        *,
        users: UserRepositoryPort,
        roles: RoleRepositoryPort,
        audit_logger: AuditLogWriter,
        credentials: CredentialService,
    ):
        self.users = users
        self.roles = roles
        self.audit_logger = audit_logger
        self.credentials = credentials

    async def list_users(self, query: UserListQuery):
        return await self.users.list(query)

    async def create_user(self, command: CreateUserCommand, actor_user_id: int, request_meta: RequestMeta):
        ensure_not_exists(await self.users.exists_by_account(command.account), "user already exists")

        open_id = self.credentials.generate_openid(command.account, str(get_timestamp()))
        user = await self.users.create(
            account=command.account,
            password=self.credentials.hash_password(command.password),
            open_id=open_id,
        )

        await record_action(self.audit_logger, actor_user_id, request_meta, f"New User [{command.account}] is created")
        return user

    async def update_user(self, command: UpdateUserCommand, actor_user_id: int, request_meta: RequestMeta):
        user = await self.users.get_by_id(command.user_id)
        ensure_exists(user, "user not found")

        before = {
            "id": user.id,
            "account": user.account,
            "open_id": user.open_id,
            "status": user.status,
        }
        updates = command.as_changes()
        if "password" in updates:
            updates["password"] = self.credentials.hash_password(updates["password"])
        updated_user = await self.users.update(command.user_id, **updates)
        after = {
            "id": updated_user.id,
            "account": updated_user.account,
            "open_id": updated_user.open_id,
            "status": updated_user.status,
        }

        await record_action(self.audit_logger, actor_user_id, request_meta, f"Users [{before}] is change to [{after}]")
        return updated_user

    async def assign_role(self, binding: UserRoleBinding, actor_user_id: int, request_meta: RequestMeta):
        user = await self.users.find(binding.user)
        ensure_exists(user, "user not found")

        role = await self.roles.find(binding.role)
        ensure_exists(role, "role not found")
        ensure_relation_absent(await self.users.has_role(user, role), "role already assigned")

        await self.users.add_role(user, role)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"User [{user.account}] add Role [{role.role_name}]")
        return user, role

    async def remove_role(self, binding: UserRoleBinding, actor_user_id: int, request_meta: RequestMeta):
        user = await self.users.find(binding.user)
        ensure_exists(user, "user not found")

        role = await self.roles.find(binding.role)
        ensure_exists(role, "role not found")
        ensure_relation_present(await self.users.has_role(user, role), "role not assigned")

        await self.users.remove_role(user, role)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"User [{user.account}] remove Role [{role.role_name}]")
        return user, role
