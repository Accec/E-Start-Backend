import importlib
import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch, sentinel


SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


CASES = (
    ("users", "UserRepository", "User", {"user_id": "id", "account": "account"},
     {"user_id": 7, "account": "alice"}),
    ("roles", "RoleRepository", "Role", {"role_id": "id", "role_name": "role_name"},
     {"role_id": 7, "role_name": "admin"}),
    ("permissions", "PermissionRepository", "Permission",
     {"permission_id": "id", "permission_title": "permission_title"},
     {"permission_id": 7, "permission_title": "manage-users"}),
    ("endpoints", "EndpointRepository", "Endpoint",
     {"endpoint_id": "id", "endpoint_path": "endpoint", "method": "method"},
     {"endpoint_id": 7, "endpoint_path": "/api/v1/roles", "method": "GET"}),
)


class IdentityRepositoryTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.repositories = [
            (importlib.import_module(f"domains.identity_access.repositories.{module}"),
             repository, model, fields, values)
            for module, repository, model, fields, values in CASES
        ]

    async def test_find_preserves_single_and_combined_conditions(self):
        for module, repository, model_name, fields, values in self.repositories:
            for selected in [*({key: value} for key, value in values.items()), values]:
                arguments = {key: selected.get(key) for key in fields}
                expected = {fields[key]: value for key, value in selected.items()}
                with self.subTest(repository=repository, arguments=arguments):
                    with patch.object(module, model_name) as model:
                        model.get_or_none = AsyncMock(return_value=sentinel.record)
                        result = await getattr(module, repository)().find(**arguments)
                    self.assertIs(result, sentinel.record)
                    model.get_or_none.assert_awaited_once_with(**expected)

    async def test_conflicting_conditions_do_not_fall_back_to_id_lookup(self):
        for module, repository, model_name, fields, values in self.repositories:
            with self.subTest(repository=repository):
                with patch.object(module, model_name) as model:
                    model.get_or_none = AsyncMock(return_value=None)
                    result = await getattr(module, repository)().find(**values)
                self.assertIsNone(result)
                model.get_or_none.assert_awaited_once_with(
                    **{fields[key]: value for key, value in values.items()},
                )

    async def test_empty_find_does_not_query(self):
        for module, repository, model_name, fields, _ in self.repositories:
            for arguments in ({}, {key: None for key in fields}):
                with self.subTest(repository=repository, arguments=arguments):
                    with patch.object(module, model_name) as model:
                        result = await getattr(module, repository)().find(**arguments)
                    self.assertIsNone(result)
                    model.get_or_none.assert_not_called()
                    model.filter.assert_not_called()
                    model.all.assert_not_called()

    async def test_list_preserves_filters_and_pagination(self):
        for module, repository, model_name, fields, values in self.repositories:
            for selected in [*({key: value} for key, value in values.items()), values]:
                arguments = {key: selected.get(key) for key in fields}
                expected = {fields[key]: value for key, value in selected.items()}
                with self.subTest(repository=repository, arguments=arguments):
                    with (
                        patch.object(module, model_name) as model,
                        patch.object(module, "paginate_query", new_callable=AsyncMock,
                                     return_value=sentinel.page) as paginate,
                    ):
                        result = await getattr(module, repository)().list(
                            **arguments, page=3, page_size=7,
                        )
                    self.assertIs(result, sentinel.page)
                    model.filter.assert_called_once_with(**expected)
                    model.all.assert_not_called()
                    paginate.assert_awaited_once_with(model.filter.return_value, 3, 7)

    async def test_empty_list_uses_all_with_default_pagination(self):
        for module, repository, model_name, fields, _ in self.repositories:
            with self.subTest(repository=repository):
                with (
                    patch.object(module, model_name) as model,
                    patch.object(module, "paginate_query", new_callable=AsyncMock,
                                 return_value=sentinel.page) as paginate,
                ):
                    result = await getattr(module, repository)().list(
                        **{key: None for key in fields},
                    )
                self.assertIs(result, sentinel.page)
                model.all.assert_called_once_with()
                model.filter.assert_not_called()
                paginate.assert_awaited_once_with(model.all.return_value, 1, 20)

    async def test_find_and_list_keep_zero_and_empty_string(self):
        for module, repository, model_name, fields, _ in self.repositories:
            arguments = {key: 0 if key.endswith("_id") else "" for key in fields}
            expected = {fields[key]: value for key, value in arguments.items()}
            with self.subTest(repository=repository):
                with (
                    patch.object(module, model_name) as model,
                    patch.object(module, "paginate_query", new_callable=AsyncMock) as paginate,
                ):
                    model.get_or_none = AsyncMock(return_value=sentinel.record)
                    instance = getattr(module, repository)()
                    await instance.find(**arguments)
                    await instance.list(**arguments)
                model.get_or_none.assert_awaited_once_with(**expected)
                model.filter.assert_called_once_with(**expected)
                model.all.assert_not_called()
                paginate.assert_awaited_once_with(model.filter.return_value, 1, 20)

    async def test_empty_delete_returns_zero_without_sql(self):
        for module, repository, model_name, fields, _ in self.repositories[1:3]:
            for arguments in ({}, {key: None for key in fields}):
                with self.subTest(repository=repository, arguments=arguments):
                    with patch.object(module, model_name) as model:
                        result = await getattr(module, repository)().delete(**arguments)
                    self.assertEqual(result, 0)
                    model.filter.assert_not_called()
                    model.all.assert_not_called()

    async def test_delete_preserves_single_combined_and_zero_conditions(self):
        for module, repository, model_name, fields, values in self.repositories[1:3]:
            zero_values = {key: 0 if key.endswith("_id") else "" for key in fields}
            for selected in [*({key: value} for key, value in values.items()), values, zero_values]:
                with self.subTest(repository=repository, arguments=selected):
                    with patch.object(module, model_name) as model:
                        model.filter.return_value.delete = AsyncMock(return_value=2)
                        result = await getattr(module, repository)().delete(**selected)
                    self.assertEqual(result, 2)
                    model.filter.assert_called_once_with(
                        **{fields[key]: value for key, value in selected.items()},
                    )
                    model.filter.return_value.delete.assert_awaited_once_with()

    def test_changed_interfaces_have_explicit_typed_keyword_only_parameters(self):
        for module, repository, _, _, _ in self.repositories:
            instance = getattr(module, repository)()
            methods = ("find", "list", "delete") if hasattr(instance, "delete") else ("find", "list")
            for method in methods:
                with self.subTest(repository=repository, method=method):
                    for parameter in inspect.signature(getattr(instance, method)).parameters.values():
                        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
                        self.assertIsNot(parameter.annotation, inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
