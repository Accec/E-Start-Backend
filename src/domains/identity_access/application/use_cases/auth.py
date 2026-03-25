import datetime

from core.constants import ROLE_USER
from ..ports import AuditLogWriter, CredentialService, RoleRepositoryPort, TokenIssuer, UserRepositoryPort
from ...domain import RequestMeta, RoleReference
from ...domain.errors import AuthenticationFailedError, UserInactiveError
from ...domain.policies import ensure_exists, ensure_not_exists, validate_login_candidate
from ._audit import record_action


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepositoryPort,
        roles: RoleRepositoryPort,
        audit_logger: AuditLogWriter,
        credentials: CredentialService,
        token_issuer: TokenIssuer,
        token_ttl_seconds: int = 0,
    ):
        self.users = users
        self.roles = roles
        self.audit_logger = audit_logger
        self.credentials = credentials
        self.token_issuer = token_issuer
        self.token_ttl_seconds = token_ttl_seconds

    async def login(self, account: str, password: str, request_meta: RequestMeta):
        user = await self.users.get_by_account(account)
        password_is_valid = self.credentials.verify_password(password, user.password) if user else False

        try:
            validate_login_candidate(user, password_is_valid)
        except UserInactiveError:
            if user:
                await record_action(self.audit_logger, user.id, request_meta, "Ban")
            raise
        except AuthenticationFailedError:
            if user:
                await record_action(self.audit_logger, user.id, request_meta, "Login failed!")
            raise

        if self.credentials.needs_rehash(user.password):
            user = await self.users.update(user.id, password=self.credentials.hash_password(password))

        await record_action(self.audit_logger, user.id, request_meta, "Login successfully!")
        return self.token_issuer.issue_token(user.id, self.token_ttl_seconds)

    async def register(self, account: str, password: str, request_meta: RequestMeta):
        ensure_not_exists(await self.users.exists_by_account(account), "user already exists")

        open_id = self.credentials.generate_openid(account, str(datetime.datetime.now(datetime.UTC).timestamp() * 1000))
        user = await self.users.create(
            account=account,
            password=self.credentials.hash_password(password),
            open_id=open_id,
        )

        role = await self.roles.find(RoleReference(role_name=ROLE_USER))
        ensure_exists(role, "default user role not found")
        await self.users.add_role(user, role)

        await record_action(self.audit_logger, user.id, request_meta, "Register successfully!")
        return user
