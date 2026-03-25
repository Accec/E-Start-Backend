from dataclasses import dataclass

from core.constants import ROLE_ADMIN, ROLE_USER
from core.time import get_timestamp

from ..ports import CredentialService, RoleRepositoryPort, UserRepositoryPort
from ...domain import RoleReference


@dataclass(frozen=True, slots=True)
class RoleBootstrapResult:
    role_name: str
    created: bool


@dataclass(frozen=True, slots=True)
class AdminBootstrapResult:
    account: str
    password: str | None
    created: bool
    role_assigned: bool


class BootstrapService:
    def __init__(self, *, users: UserRepositoryPort, roles: RoleRepositoryPort, credentials: CredentialService):
        self.users = users
        self.roles = roles
        self.credentials = credentials

    async def ensure_role(self, role_name: str):
        role = await self.roles.find(RoleReference(role_name=role_name))
        if role is not None:
            return RoleBootstrapResult(role_name=role_name, created=False)

        await self.roles.create(role_name)
        return RoleBootstrapResult(role_name=role_name, created=True)

    async def ensure_default_roles(self):
        return [
            await self.ensure_role(ROLE_ADMIN),
            await self.ensure_role(ROLE_USER),
        ]

    async def create_admin(self, username: str | None = None, password: str | None = None):
        await self.ensure_default_roles()

        account = username or "admin"
        user = await self.users.get_by_account(account)
        created = False
        issued_password = None

        if user is None:
            issued_password = password or self.credentials.generate_password()
            open_id = self.credentials.generate_openid(account, str(get_timestamp()))
            user = await self.users.create(
                account=account,
                password=self.credentials.hash_password(issued_password),
                open_id=open_id,
            )
            created = True

        admin_role = await self.roles.find(RoleReference(role_name=ROLE_ADMIN))
        role_assigned = False
        if admin_role is not None and not await self.users.has_role(user, admin_role):
            await self.users.add_role(user, admin_role)
            role_assigned = True

        return AdminBootstrapResult(
            account=account,
            password=issued_password,
            created=created,
            role_assigned=role_assigned,
        )
