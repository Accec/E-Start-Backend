import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.constants import ROLE_USER
from domains.identity_access.services.auth import AuthService
from domains.identity_access.services.bootstrap import BootstrapService
from domains.identity_access.services.endpoints import EndpointAdminService
from domains.identity_access.services.permissions import PermissionAdminService
from domains.identity_access.services.roles import RoleAdminService
from domains.identity_access.services.users import UserAdminService
from domains.identity_access.audit import RequestMeta
from domains.identity_access.errors import (
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
)


class IdentityServiceParametersTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.users = AsyncMock()
        self.roles = AsyncMock()
        self.permissions = AsyncMock()
        self.endpoints = AsyncMock()
        self.audit = AsyncMock()
        self.credentials = Mock()
        self.credentials.hash_password.return_value = "hashed-password"
        self.credentials.generate_openid.return_value = "new-open-id"
        self.meta = RequestMeta(api="/api/v1/admin/test", ip="127.0.0.1", ua="unittest")
        self.actor = {"actor_user_id": 9, "request_meta": self.meta}
        self.user = SimpleNamespace(id=1, account="alice", open_id="open-id", status=1)
        self.role = SimpleNamespace(id=2, role_name="reader")
        self.permission = SimpleNamespace(id=3, permission_title="read")
        self.endpoint = SimpleNamespace(id=4, endpoint="/items")
        self.users.find.return_value = self.user
        self.roles.find.return_value = self.role
        self.permissions.find.return_value = self.permission
        self.endpoints.find.return_value = self.endpoint
        self.user_service = UserAdminService(
            users=self.users, roles=self.roles, audit_logger=self.audit, credentials=self.credentials,
        )
        self.role_service = RoleAdminService(
            roles=self.roles, permissions=self.permissions, audit_logger=self.audit,
        )
        self.permission_service = PermissionAdminService(permissions=self.permissions, audit_logger=self.audit)
        self.endpoint_service = EndpointAdminService(
            endpoints=self.endpoints, permissions=self.permissions, audit_logger=self.audit,
        )

    async def test_lists_forward_all_filters_and_pagination(self):
        cases = (
            (self.user_service.list_users, self.users, {"user_id": 1, "account": "alice"}),
            (self.role_service.list_roles, self.roles, {"role_id": 2, "role_name": "reader"}),
            (self.permission_service.list_permissions, self.permissions,
             {"permission_id": 3, "permission_title": "read"}),
            (self.endpoint_service.list_endpoints, self.endpoints,
             {"endpoint_id": 4, "endpoint_path": "/items", "method": "GET"}),
        )
        for method, repository, filters in cases:
            with self.subTest(method=method.__name__):
                page = object()
                repository.list.return_value = page
                self.assertIs(await method(**filters, page=2, page_size=7), page)
                repository.list.assert_awaited_once_with(**filters, page=2, page_size=7)

    async def test_list_defaults_preserve_unfiltered_pagination(self):
        await self.user_service.list_users()
        self.users.list.assert_awaited_once_with(user_id=None, account=None, page=1, page_size=20)

    async def test_create_user_hashes_password_and_preserves_audit_metadata(self):
        self.users.exists_by_account.return_value = False
        self.users.create.return_value = self.user
        result = await self.user_service.create_user(account="alice", password="Secret123!", **self.actor)
        self.assertIs(result, self.user)
        self.credentials.hash_password.assert_called_once_with("Secret123!")
        self.users.create.assert_awaited_once_with(
            account="alice", password="hashed-password", open_id="new-open-id",
        )
        record = self.audit.record.call_args.args[0]
        self.assertEqual((record.user_id, record.api, record.ip, record.ua),
                         (9, self.meta.api, self.meta.ip, self.meta.ua))
        self.assertEqual(record.action, "New User [alice] is created")

    async def test_update_user_omits_none_values_without_hashing(self):
        self.users.get_by_id.return_value = self.user
        self.users.update.return_value = self.user
        result = await self.user_service.update_user(user_id=1, account=None, password=None, **self.actor)
        self.assertIs(result, self.user)
        self.users.update.assert_awaited_once_with(1)
        self.credentials.hash_password.assert_not_called()
        values = {"id": 1, "account": "alice", "open_id": "open-id", "status": 1}
        self.assertEqual(self.audit.record.call_args.args[0].action, f"Users [{values}] is change to [{values}]")

    async def test_update_user_hashes_supplied_password_and_keeps_falsy_account(self):
        self.users.get_by_id.return_value = self.user
        self.users.update.return_value = self.user
        await self.user_service.update_user(user_id=1, account="", password="Secret123!", **self.actor)
        self.credentials.hash_password.assert_called_once_with("Secret123!")
        self.users.update.assert_awaited_once_with(1, account="", password="hashed-password")

    async def test_empty_delete_conditions_do_not_reach_repositories(self):
        for method, repository in (
            (self.role_service.delete_role, self.roles),
            (self.permission_service.delete_permission, self.permissions),
        ):
            with self.subTest(method=method.__name__):
                with self.assertRaises(ResourceNotFoundError):
                    await method(**self.actor)
                repository.find.assert_not_awaited()
                repository.delete.assert_not_awaited()
        self.audit.record.assert_not_awaited()

    async def test_delete_keeps_combined_conditions_and_original_audit_text(self):
        await self.role_service.delete_role(role_id=2, role_name="reader", **self.actor)
        self.roles.find.assert_awaited_once_with(role_id=2, role_name="reader")
        self.roles.delete.assert_awaited_once_with(role_id=2, role_name="reader")
        self.assertEqual(self.audit.record.call_args.args[0].action,
                         "Role [{'id': 2, 'role_name': 'reader'}] is deleted")

        await self.permission_service.delete_permission(permission_id=3, permission_title="read", **self.actor)
        self.permissions.find.assert_awaited_once_with(permission_id=3, permission_title="read")
        self.permissions.delete.assert_awaited_once_with(permission_id=3, permission_title="read")
        self.assertEqual(self.audit.record.call_args.args[0].action,
                         "Permission [{'id': 3, 'permission_title': 'read'}] is deleted")

    async def test_missing_delete_target_does_not_delete_or_audit(self):
        self.roles.find.return_value = None
        with self.assertRaises(ResourceNotFoundError):
            await self.role_service.delete_role(role_id=99, **self.actor)
        self.roles.delete.assert_not_awaited()
        self.audit.record.assert_not_awaited()

    async def test_assign_role_forwards_both_resource_identifiers(self):
        self.users.has_role.return_value = False
        result = await self.user_service.assign_role(
            user_id=1, account="alice", role_id=2, role_name="reader", **self.actor,
        )
        self.assertEqual(result, (self.user, self.role))
        self.users.find.assert_awaited_once_with(user_id=1, account="alice")
        self.roles.find.assert_awaited_once_with(role_id=2, role_name="reader")
        self.users.add_role.assert_awaited_once_with(self.user, self.role)
        self.assertEqual(self.audit.record.call_args.args[0].action, "User [alice] add Role [reader]")

    async def test_relation_guards_prevent_duplicate_additions_and_missing_removals(self):
        user_role = {"user_id": 1, "role_id": 2}
        role_permission = {"role_id": 2, "permission_id": 3}
        endpoint_permission = {"endpoint_id": 4, "permission_id": 3}
        cases = (
            (self.user_service.assign_role, self.users.has_role, True,
             self.users.add_role, RelationAlreadyExistsError, user_role),
            (self.user_service.remove_role, self.users.has_role, False,
             self.users.remove_role, RelationNotFoundError, user_role),
            (self.role_service.add_permission, self.roles.has_permission, True,
             self.roles.add_permission, RelationAlreadyExistsError, role_permission),
            (self.role_service.remove_permission, self.roles.has_permission, False,
             self.roles.remove_permission, RelationNotFoundError, role_permission),
            (self.endpoint_service.add_permission, self.endpoints.has_permission, True,
             self.endpoints.add_permission, RelationAlreadyExistsError, endpoint_permission),
            (self.endpoint_service.remove_permission, self.endpoints.has_permission, False,
             self.endpoints.remove_permission, RelationNotFoundError, endpoint_permission),
        )
        for method, relation_check, exists, mutation, error, identifiers in cases:
            with self.subTest(service=type(method.__self__).__name__, method=method.__name__):
                relation_check.return_value = exists
                with self.assertRaises(error):
                    await method(**identifiers, **self.actor)
                mutation.assert_not_awaited()
        self.audit.record.assert_not_awaited()

    async def test_endpoint_binding_preserves_method_and_permission_conditions(self):
        self.endpoints.has_permission.return_value = False
        result = await self.endpoint_service.add_permission(
            endpoint_id=4, endpoint_path="/items", method="GET",
            permission_id=3, permission_title="read", **self.actor,
        )
        self.assertEqual(result, (self.endpoint, self.permission))
        self.endpoints.find.assert_awaited_once_with(endpoint_id=4, endpoint_path="/items", method="GET")
        self.permissions.find.assert_awaited_once_with(permission_id=3, permission_title="read")
        self.endpoints.add_permission.assert_awaited_once_with(self.endpoint, self.permission)
        self.assertEqual(self.audit.record.call_args.args[0].action, "Endpoint [/items] add permission [read]")

    async def test_registration_finds_default_role_by_name(self):
        self.users.exists_by_account.return_value = False
        self.users.create.return_value = self.user
        service = AuthService(
            users=self.users, roles=self.roles, audit_logger=self.audit,
            credentials=self.credentials, token_issuer=Mock(),
        )
        result = await service.register("alice", "Secret123!", self.meta)
        self.assertIs(result, self.user)
        self.roles.find.assert_awaited_once_with(role_name=ROLE_USER)
        self.users.add_role.assert_awaited_once_with(self.user, self.role)
        self.assertEqual(self.audit.record.call_args.args[0].action, "Register successfully!")

    async def test_role_initialization_finds_by_name_and_is_idempotent(self):
        service = BootstrapService(users=self.users, roles=self.roles, credentials=self.credentials)
        result = await service.ensure_role("reader")
        self.roles.find.assert_awaited_once_with(role_name="reader")
        self.roles.create.assert_not_awaited()
        self.assertEqual((result.role_name, result.created), ("reader", False))


if __name__ == "__main__":
    unittest.main()
