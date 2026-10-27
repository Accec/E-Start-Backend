from core.time import get_timestamp

from ..ports import AuditLogWriter, CredentialService, RoleRepositoryPort, UserRepositoryPort
from ..audit import RequestMeta, record_action
from ..policies import ensure_exists, ensure_not_exists, ensure_relation_absent, ensure_relation_present


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

    async def list_users(
        self, *, user_id: int | None = None, account: str | None = None,
        page: int = 1, page_size: int = 20,
    ):
        return await self.users.list(user_id=user_id, account=account, page=page, page_size=page_size)

    async def create_user(
        self, *, account: str | None, password: str | None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        ensure_not_exists(await self.users.exists_by_account(account), "user already exists")

        open_id = self.credentials.generate_openid(account, str(get_timestamp()))
        user = await self.users.create(
            account=account,
            password=self.credentials.hash_password(password),
            open_id=open_id,
        )

        await record_action(self.audit_logger, actor_user_id, request_meta, f"New User [{account}] is created")
        return user

    async def update_user(
        self, *, user_id: int | None, account: str | None = None, password: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        user = await self.users.get_by_id(user_id)
        ensure_exists(user, "user not found")

        before = {
            "id": user.id,
            "account": user.account,
            "open_id": user.open_id,
            "status": user.status,
        }
        updates = {}
        if account is not None:
            updates["account"] = account
        if password is not None:
            updates["password"] = self.credentials.hash_password(password)
        updated_user = await self.users.update(user_id, **updates)
        after = {
            "id": updated_user.id,
            "account": updated_user.account,
            "open_id": updated_user.open_id,
            "status": updated_user.status,
        }

        await record_action(self.audit_logger, actor_user_id, request_meta, f"Users [{before}] is change to [{after}]")
        return updated_user

    async def assign_role(
        self, *, user_id: int | None = None, account: str | None = None,
        role_id: int | None = None, role_name: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        user = await self.users.find(user_id=user_id, account=account)
        ensure_exists(user, "user not found")

        role = await self.roles.find(role_id=role_id, role_name=role_name)
        ensure_exists(role, "role not found")
        ensure_relation_absent(await self.users.has_role(user, role), "role already assigned")

        await self.users.add_role(user, role)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"User [{user.account}] add Role [{role.role_name}]")
        return user, role

    async def remove_role(
        self, *, user_id: int | None = None, account: str | None = None,
        role_id: int | None = None, role_name: str | None = None,
        actor_user_id: int, request_meta: RequestMeta,
    ):
        user = await self.users.find(user_id=user_id, account=account)
        ensure_exists(user, "user not found")

        role = await self.roles.find(role_id=role_id, role_name=role_name)
        ensure_exists(role, "role not found")
        ensure_relation_present(await self.users.has_role(user, role), "role not assigned")

        await self.users.remove_role(user, role)
        await record_action(self.audit_logger, actor_user_id, request_meta, f"User [{user.account}] remove Role [{role.role_name}]")
        return user, role
