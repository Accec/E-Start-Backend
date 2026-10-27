import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pydantic import ValidationError
from sanic_ext.exceptions import ValidationError as HttpValidationError

from core.responses import InvalidArgumentsError, InvalidCredentialsError
from domains.identity_access.audit import RequestMeta
from domains.identity_access.errors import (
    DuplicateResourceError,
    AuthenticationFailedError,
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
)
from domains.identity_access.controller.endpoints.api import EndpointAdminController
from domains.identity_access.controller.permissions.api import PermissionAdminController
from domains.identity_access.controller.roles.api import RoleAdminController
from domains.identity_access.controller.users.api import UserAdminController
from domains.identity_access.controller.auth.api import UserAuthController
from domains.identity_access.controller.endpoints import schemas as endpoints
from domains.identity_access.controller.permissions import schemas as permissions
from domains.identity_access.controller.roles import schemas as roles
from domains.identity_access.controller.users import schemas as users
from domains.identity_access.controller.auth import schemas as auth
from domains.identity_access.controller.dashboard import schemas as dashboard


class IdentityHttpSchemaTestCase(unittest.TestCase):
    def test_http_models_have_unique_method_resource_names_without_old_aliases(self):
        renamed = {
            users: {
                "UserListQuery": "GetUserQuery", "UserListResponse": "GetUserResponse",
                "CreateUserBody": "PostUserBody", "CreateUserResponse": "PostUserResponse",
                "UpdateUserBody": "PutUserBody", "UpdateUserResponse": "PutUserResponse",
                "AssignUserRoleBody": "PostUserRoleBody", "AssignUserRoleResponse": "PostUserRoleResponse",
                "RemoveUserRoleBody": "DeleteUserRoleBody", "RemoveUserRoleResponse": "DeleteUserRoleResponse",
            },
            roles: {
                "RoleListQuery": "GetRoleQuery", "RoleListResponse": "GetRoleResponse",
                "CreateRoleBody": "PostRoleBody", "CreateRoleResponse": "PostRoleResponse",
                "UpdateRoleBody": "PutRoleBody", "UpdateRoleResponse": "PutRoleResponse",
                "AssignRolePermissionBody": "PostRolePermissionBody",
                "AssignRolePermissionResponse": "PostRolePermissionResponse",
                "RemoveRolePermissionBody": "DeleteRolePermissionBody",
                "RemoveRolePermissionResponse": "DeleteRolePermissionResponse",
            },
            permissions: {
                "PermissionListQuery": "GetPermissionQuery", "PermissionListResponse": "GetPermissionResponse",
                "CreatePermissionBody": "PostPermissionBody", "CreatePermissionResponse": "PostPermissionResponse",
                "UpdatePermissionBody": "PutPermissionBody", "UpdatePermissionResponse": "PutPermissionResponse",
            },
            endpoints: {
                "EndpointListQuery": "GetEndpointQuery", "EndpointListResponse": "GetEndpointResponse",
                "AssignEndpointPermissionBody": "PostEndpointPermissionBody",
                "AssignEndpointPermissionResponse": "PostEndpointPermissionResponse",
                "RemoveEndpointPermissionBody": "DeleteEndpointPermissionBody",
                "RemoveEndpointPermissionResponse": "DeleteEndpointPermissionResponse",
            },
            auth: {
                "LoginBody": "PostLoginBody", "LoginResponse": "PostLoginResponse",
                "RegisterBody": "PostRegisterBody", "RegisterResponse": "PostRegisterResponse",
            },
            dashboard: {"DashboardResponse": "GetDashboardResponse"},
        }
        names = []
        for module, mapping in renamed.items():
            for old, new in mapping.items():
                with self.subTest(model=new):
                    self.assertFalse(hasattr(module, old))
                    if new.endswith("Response"):
                        self.assertFalse(hasattr(module, new))
                        continue
                    self.assertEqual(getattr(module, new).__name__, new)
                    names.append(new)
        self.assertEqual(len(names), len(set(names)))

    def test_query_defaults_and_combined_fields_are_unchanged(self):
        for model in (users.GetUserQuery, roles.GetRoleQuery,
                      permissions.GetPermissionQuery, endpoints.GetEndpointQuery):
            with self.subTest(model=model.__name__):
                query = model()
                self.assertEqual((query.page, query.page_size, query.id), (1, 20, None))
        self.assertEqual(roles.GetRoleQuery(id=0, role_name="").model_dump(), {
            "page": 1, "page_size": 20, "id": 0, "role_name": "",
        })

    def test_required_nullable_and_default_fields_keep_their_original_meaning(self):
        for model in (users.PostUserBody, users.PutUserBody, roles.PostRoleBody,
                      roles.PutRoleBody, permissions.PutPermissionBody):
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError):
                    model()
        self.assertIsNone(permissions.PostPermissionBody().permission_title)
        self.assertEqual(roles.PutRoleBody(id=None, role_name=None).model_dump(), {
            "id": None, "role_name": None,
        })
        self.assertEqual(permissions.PutPermissionBody(id=None, permission_title=None).model_dump(), {
            "id": None, "permission_title": None,
        })
        self.assertTrue(users.PostUserBody.model_fields["account"].is_required())
        self.assertTrue(users.PutUserBody.model_fields["password"].is_required())
        self.assertIsNone(users.PostUserRoleBody().role)
        self.assertEqual(set(endpoints.PostEndpointPermissionBody.model_fields), {
            "id", "endpoint", "permission",
        })

    def test_user_and_auth_validators_keep_existing_constraints(self):
        valid = {"account": "alice1", "password": "Secret123!"}
        for model in (users.PostUserBody, users.PutUserBody, auth.PostRegisterBody):
            with self.subTest(model=model.__name__):
                self.assertEqual(model(**valid).account, "alice1")
                with self.assertRaises(HttpValidationError):
                    model(account="alice_", password=valid["password"])
                with self.assertRaises(HttpValidationError):
                    model(account=valid["account"], password="password1")
        self.assertEqual(auth.PostLoginBody(**valid, verify_code="12345678").verify_code, "12345678")
        self.assertEqual(auth.PostRegisterBody(**valid, verify_code="123456").verify_code, "123456")
        with self.assertRaises(ValidationError):
            auth.PostLoginBody(**valid, verify_code="123456")
        with self.assertRaises(ValidationError):
            auth.PostRegisterBody(**valid, verify_code="12345678")


class IdentityHttpMappingTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.request = SimpleNamespace(ctx=SimpleNamespace(
            user={"user_id": 91}, request_path="/api/v1/admin/test",
            real_ip="127.0.0.1", ua="unittest",
        ))
        self.metadata = RequestMeta(api="/api/v1/admin/test", ip="127.0.0.1", ua="unittest")

    async def test_login_returns_token_inside_results(self):
        login = AsyncMock(return_value="access-token")
        controller = UserAuthController(SimpleNamespace(login=login))
        body = auth.PostLoginBody(account="alice1", password="Secret123!")

        response = await controller.login(self.request, body)

        login.assert_awaited_once_with(
            account=body.account, password=body.password, request_meta=self.metadata,
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.body), {
            "code": 0, "msg": "Success", "results": {"token": "access-token"},
        })

    async def test_failed_login_uses_the_same_results_envelope(self):
        login = AsyncMock(side_effect=AuthenticationFailedError("invalid credentials"))
        controller = UserAuthController(SimpleNamespace(login=login))
        response = await controller.login(
            self.request, auth.PostLoginBody(account="alice1", password="Secret123!"),
        )
        self.assertEqual(response.status, 401)
        self.assertEqual(json.loads(response.body), {
            "code": InvalidCredentialsError.code,
            "msg": InvalidCredentialsError.msg,
            "results": None,
        })

    async def test_lists_forward_plain_keyword_filters_and_pagination(self):
        cases = (
            (UserAdminController, "list_users", users.GetUserQuery,
             {"id": 0, "account": "alice1"}, {"user_id": 0, "account": "alice1"}),
            (RoleAdminController, "list_roles", roles.GetRoleQuery,
             {"id": 2, "role_name": "admin"}, {"role_id": 2, "role_name": "admin"}),
            (PermissionAdminController, "list_permissions", permissions.GetPermissionQuery,
             {"id": 3, "permission_title": "read"}, {"permission_id": 3, "permission_title": "read"}),
            (EndpointAdminController, "list_endpoints", endpoints.GetEndpointQuery,
             {"id": 4, "endpoint": "/users", "method": "GET"},
             {"endpoint_id": 4, "endpoint_path": "/users", "method": "GET"}),
        )
        for controller_type, method, model, payload, expected in cases:
            with self.subTest(method=method):
                operation = AsyncMock(return_value=SimpleNamespace(items=[], total_items=0, total_pages=0))
                controller = controller_type(SimpleNamespace(**{method: operation}))
                response = await getattr(controller, method)(self.request, model(**payload, page=2, page_size=5))
                operation.assert_awaited_once_with(**expected, page=2, page_size=5)
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.body)["results"], [])

    async def test_create_update_and_delete_forward_fields_without_command_objects(self):
        cases = (
            (UserAdminController, "create_user", users.PostUserBody,
             {"account": "alice1", "password": "Secret123!"},
             {"account": "alice1", "password": "Secret123!"}, 201),
            (UserAdminController, "update_user", users.PutUserBody,
             {"id": 1, "account": "alice1", "password": "Secret123!"},
             {"user_id": 1, "account": "alice1", "password": "Secret123!"}, 201),
            (RoleAdminController, "create_role", roles.PostRoleBody,
             {"role_name": "admin"}, {"role_name": "admin"}, 201),
            (RoleAdminController, "update_role", roles.PutRoleBody,
             {"id": 2, "role_name": None}, {"role_id": 2, "role_name": None}, 201),
            (RoleAdminController, "delete_role", roles.DeleteRoleBody,
             {"id": 2, "role_name": "admin"}, {"role_id": 2, "role_name": "admin"}, 204),
            (PermissionAdminController, "create_permission", permissions.PostPermissionBody,
             {}, {"permission_title": None}, 201),
            (PermissionAdminController, "update_permission", permissions.PutPermissionBody,
             {"id": 3, "permission_title": None}, {"permission_id": 3, "permission_title": None}, 201),
            (PermissionAdminController, "delete_permission", permissions.DeletePermissionBody,
             {"id": 3, "permission_title": "read"}, {"permission_id": 3, "permission_title": "read"}, 204),
        )
        for controller_type, method, model, payload, expected, status in cases:
            with self.subTest(method=method):
                operation = AsyncMock()
                controller = controller_type(SimpleNamespace(**{method: operation}))
                response = await getattr(controller, method)(self.request, model(**payload))
                operation.assert_awaited_once_with(
                    **expected, actor_user_id=91, request_meta=self.metadata,
                )
                self.assertEqual(response.status, status)

    async def test_nested_bindings_expand_only_business_fields(self):
        cases = (
            (UserAdminController, "assign_role", "assign_role", users.PostUserRoleBody,
             {"id": 1, "account": "alice1", "role": {"id": 2, "role_name": "admin"}},
             {"user_id": 1, "account": "alice1", "role_id": 2, "role_name": "admin"}, 201),
            (UserAdminController, "remove_role", "remove_role", users.DeleteUserRoleBody,
             {"id": 1, "account": "alice1", "role": {"id": 2, "role_name": "admin"}},
             {"user_id": 1, "account": "alice1", "role_id": 2, "role_name": "admin"}, 204),
            (RoleAdminController, "assign_permission", "add_permission", roles.PostRolePermissionBody,
             {"id": 2, "role_name": "admin", "permission": {"id": 3, "permission_title": "read"}},
             {"role_id": 2, "role_name": "admin", "permission_id": 3, "permission_title": "read"}, 201),
            (RoleAdminController, "remove_permission", "remove_permission", roles.DeleteRolePermissionBody,
             {"id": 2, "role_name": "admin", "permission": {"id": 3, "permission_title": "read"}},
             {"role_id": 2, "role_name": "admin", "permission_id": 3, "permission_title": "read"}, 204),
            (EndpointAdminController, "assign_permission", "add_permission", endpoints.PostEndpointPermissionBody,
             {"id": 4, "endpoint": "/users", "permission": {"id": 3, "permission_title": "read"}},
             {"endpoint_id": 4, "endpoint_path": "/users", "permission_id": 3, "permission_title": "read"}, 201),
            (EndpointAdminController, "remove_permission", "remove_permission", endpoints.DeleteEndpointPermissionBody,
             {"id": 4, "endpoint": "/users", "permission": {"id": 3, "permission_title": "read"}},
             {"endpoint_id": 4, "endpoint_path": "/users", "permission_id": 3, "permission_title": "read"}, 204),
        )
        for controller_type, method, service_method, model, payload, expected, status in cases:
            with self.subTest(controller=controller_type.__name__, method=method):
                operation = AsyncMock()
                controller = controller_type(SimpleNamespace(**{service_method: operation}))
                response = await getattr(controller, method)(self.request, model(**payload))
                operation.assert_awaited_once_with(
                    **expected, actor_user_id=91, request_meta=self.metadata,
                )
                self.assertEqual(response.status, status)

    async def test_missing_nested_binding_returns_400_without_calling_service(self):
        cases = (
            (UserAdminController, "assign_role", "assign_role", users.PostUserRoleBody),
            (UserAdminController, "remove_role", "remove_role", users.DeleteUserRoleBody),
            (RoleAdminController, "assign_permission", "add_permission", roles.PostRolePermissionBody),
            (RoleAdminController, "remove_permission", "remove_permission", roles.DeleteRolePermissionBody),
            (EndpointAdminController, "assign_permission", "add_permission", endpoints.PostEndpointPermissionBody),
            (EndpointAdminController, "remove_permission", "remove_permission", endpoints.DeleteEndpointPermissionBody),
        )
        for controller_type, method, service_method, model in cases:
            with self.subTest(controller=controller_type.__name__, method=method):
                operation = AsyncMock()
                controller = controller_type(SimpleNamespace(**{service_method: operation}))
                response = await getattr(controller, method)(self.request, model(id=1))
                operation.assert_not_awaited()
                self.assertEqual(response.status, 400)
                self.assertEqual(json.loads(response.body), {
                    "code": InvalidArgumentsError.code, "msg": InvalidArgumentsError.msg, "results": None,
                })

    async def test_existing_business_errors_keep_their_http_mapping(self):
        cases = (
            ("create_role", roles.PostRoleBody(role_name="admin"), DuplicateResourceError),
            ("update_role", roles.PutRoleBody(id=1, role_name="admin"), ResourceNotFoundError),
            ("assign_permission", roles.PostRolePermissionBody(id=1, permission={"id": 2}),
             RelationAlreadyExistsError),
            ("remove_permission", roles.DeleteRolePermissionBody(id=1, permission={"id": 2}),
             RelationNotFoundError),
        )
        for method, body, error in cases:
            with self.subTest(method=method, error=error.__name__):
                service_method = "add_permission" if method == "assign_permission" else method
                operation = AsyncMock(side_effect=error("existing error"))
                controller = RoleAdminController(SimpleNamespace(**{service_method: operation}))
                response = await getattr(controller, method)(self.request, body)
                self.assertEqual(response.status, 400)
                self.assertEqual(json.loads(response.body)["code"], InvalidArgumentsError.code)


if __name__ == "__main__":
    unittest.main()
