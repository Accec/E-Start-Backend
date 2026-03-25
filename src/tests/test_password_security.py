import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.constants import UserStatus
from domains.identity_access.application.use_cases.auth import AuthService
from domains.identity_access.domain.errors import AuthenticationFailedError
from domains.identity_access.domain.request_meta import RequestMeta
from infra.security.passwords import generate_openid, hash_password, needs_rehash, verify_password


def legacy_hash_password(password: str) -> str:
    import hashlib

    hashed = hashlib.md5(password.encode()).hexdigest()
    hashed = str(password + hashed + password + hashed + hashed + password)
    hashed = hashlib.md5(hashed.encode() + password.encode() + hashed.encode()).hexdigest()
    hashed = str(hashed + password + hashed + hashed + password + hashed)
    hashed = hashlib.md5(password.encode() + hashed.encode() + password.encode()).hexdigest()
    hashed = str(password + hashed + password + hashed + hashed + password)
    hashed = hashlib.md5(hashed.encode() + password.encode() + hashed.encode()).hexdigest()
    hashed = str(hashed + password + hashed + hashed + password + hashed)
    hashed = hashlib.md5(password.encode() + hashed.encode() + password.encode()).hexdigest()
    return hashed


class FakeUserRepository:
    def __init__(self, user):
        self.user = user
        self.update_calls: list[dict[str, str | int]] = []

    async def get_by_account(self, account: str):
        if self.user and self.user.account == account:
            return self.user
        return None

    async def update(self, user_id: int, *, account: str | None = None, password: str | None = None):
        self.update_calls.append({"user_id": user_id, "account": account, "password": password})
        if account is not None:
            self.user.account = account
        if password is not None:
            self.user.password = password
        return self.user


class FakeRoleRepository:
    pass


class FakeAuditLogger:
    def __init__(self):
        self.records = []

    async def record(self, record):
        self.records.append(record)


class FakeTokenIssuer:
    def issue_token(self, user_id: int, exp_seconds: int):
        return f"token-{user_id}-{exp_seconds}"


class CredentialServiceStub:
    def hash_password(self, password: str):
        return hash_password(password)

    def verify_password(self, password: str, password_hash: str):
        return verify_password(password, password_hash)

    def needs_rehash(self, password_hash: str):
        return needs_rehash(password_hash)

    def generate_openid(self, account: str, salt: str):
        return generate_openid(account, salt)

    def generate_password(self, length: int = 12):
        return "X" * length


class PasswordSecurityTestCase(unittest.TestCase):
    def test_current_password_hash_uses_argon_and_verifies(self):
        password_hash = hash_password("Secret123!")
        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertTrue(verify_password("Secret123!", password_hash))
        self.assertFalse(verify_password("Wrong123!", password_hash))
        self.assertFalse(needs_rehash(password_hash))

    def test_legacy_hash_still_verifies_but_requires_rehash(self):
        legacy_hash = legacy_hash_password("Secret123!")
        self.assertTrue(verify_password("Secret123!", legacy_hash))
        self.assertTrue(needs_rehash(legacy_hash))


class AuthServicePasswordMigrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_login_rehashes_legacy_password_after_success(self):
        credentials = CredentialServiceStub()
        user = SimpleNamespace(
            id=1,
            account="alice",
            password=legacy_hash_password("Secret123!"),
            status=UserStatus.ACTIVE,
        )
        users = FakeUserRepository(user)
        audit_logger = FakeAuditLogger()
        service = AuthService(
            users=users,
            roles=FakeRoleRepository(),
            audit_logger=audit_logger,
            credentials=credentials,
            token_issuer=FakeTokenIssuer(),
            token_ttl_seconds=600,
        )

        token = await service.login(
            "alice",
            "Secret123!",
            RequestMeta(api="/api/v1/user/login", ip="127.0.0.1", ua="unittest"),
        )

        self.assertEqual(token, "token-1-600")
        self.assertEqual(len(users.update_calls), 1)
        self.assertTrue(user.password.startswith("$argon2id$"))
        self.assertFalse(needs_rehash(user.password))
        self.assertEqual(audit_logger.records[-1].action, "Login successfully!")

    async def test_login_with_current_hash_does_not_rehash(self):
        credentials = CredentialServiceStub()
        user = SimpleNamespace(
            id=2,
            account="bob",
            password=credentials.hash_password("Secret123!"),
            status=UserStatus.ACTIVE,
        )
        users = FakeUserRepository(user)
        service = AuthService(
            users=users,
            roles=FakeRoleRepository(),
            audit_logger=FakeAuditLogger(),
            credentials=credentials,
            token_issuer=FakeTokenIssuer(),
            token_ttl_seconds=600,
        )

        token = await service.login(
            "bob",
            "Secret123!",
            RequestMeta(api="/api/v1/user/login", ip="127.0.0.1", ua="unittest"),
        )

        self.assertEqual(token, "token-2-600")
        self.assertEqual(users.update_calls, [])

    async def test_login_with_wrong_password_fails(self):
        credentials = CredentialServiceStub()
        user = SimpleNamespace(
            id=3,
            account="carol",
            password=credentials.hash_password("Secret123!"),
            status=UserStatus.ACTIVE,
        )
        users = FakeUserRepository(user)
        service = AuthService(
            users=users,
            roles=FakeRoleRepository(),
            audit_logger=FakeAuditLogger(),
            credentials=credentials,
            token_issuer=FakeTokenIssuer(),
            token_ttl_seconds=600,
        )

        with self.assertRaises(AuthenticationFailedError):
            await service.login(
                "carol",
                "Wrong123!",
                RequestMeta(api="/api/v1/user/login", ip="127.0.0.1", ua="unittest"),
            )

        self.assertEqual(users.update_calls, [])


if __name__ == "__main__":
    unittest.main()
