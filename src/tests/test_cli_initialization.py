import asyncio
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch


SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class CliInitializationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.ops = importlib.import_module("scripts.ops.cli")
            from click.testing import CliRunner
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"CLI dependencies are unavailable: {exc}") from exc
        cls.runner_type = CliRunner

    def setUp(self):
        self.service = Mock(ensure_default_roles=AsyncMock(), create_admin=AsyncMock())
        self.constructors = {}
        for name in ("UserRepository", "RoleRepository", "PasswordCredentialService", "BootstrapService"):
            patcher = patch.object(self.ops, name)
            self.constructors[name] = patcher.start()
            self.addCleanup(patcher.stop)
        self.constructors["BootstrapService"].return_value = self.service
        for target in ("infra.redis.RedisClient", "infra.scheduler.Scheduler", "infra.security.jwt.JwtAuth"):
            patcher = patch(target, side_effect=AssertionError(f"Unrelated dependency constructed: {target}"))
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in ("init", "close_connections"):
            patcher = patch.object(self.ops.Tortoise, name, new_callable=AsyncMock)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def assert_minimal_dependencies(self):
        self.constructors["BootstrapService"].assert_called_once_with(
            users=self.constructors["UserRepository"].return_value,
            roles=self.constructors["RoleRepository"].return_value,
            credentials=self.constructors["PasswordCredentialService"].return_value,
        )
        for name in ("UserRepository", "RoleRepository", "PasswordCredentialService"):
            self.constructors[name].assert_called_once_with()

    def test_seed_roles_only_constructs_its_business_dependencies(self):
        expected = [SimpleNamespace(role_name="admin", created=True)]
        self.service.ensure_default_roles.return_value = expected

        self.assertEqual(asyncio.run(self.ops.seed_default_roles()), expected)
        self.service.ensure_default_roles.assert_awaited_once_with()
        self.assert_minimal_dependencies()

    def test_create_admin_preserves_arguments_and_output(self):
        self.service.create_admin.return_value = SimpleNamespace(
            created=True, account="alice", password="example-password", role_assigned=True,
        )
        result = self.runner_type().invoke(
            self.ops.cli, ["create_admin", "--username", "alice", "--password", "example-password"],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "Admin created [account: alice - password: example-password].\n")
        self.service.create_admin.assert_awaited_once_with(username="alice", password="example-password")
        self.assert_minimal_dependencies()
        self.init.assert_awaited_once()
        self.close_connections.assert_awaited_once()

    def test_seed_command_preserves_output(self):
        self.service.ensure_default_roles.return_value = [
            SimpleNamespace(role_name="admin", created=False),
            SimpleNamespace(role_name="user", created=True),
        ]
        result = self.runner_type().invoke(self.ops.cli, ["seed_identity_access"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "Role admin already exists.\nRole user created.\n")
        self.assert_minimal_dependencies()
        self.close_connections.assert_awaited_once()

    def test_failed_admin_creation_still_closes_database(self):
        self.service.create_admin.side_effect = RuntimeError("database operation failed")
        result = self.runner_type().invoke(self.ops.cli, ["create_admin"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIsInstance(result.exception, RuntimeError)
        self.close_connections.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
