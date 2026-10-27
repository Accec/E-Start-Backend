import ast
import importlib.util
import os
import re
import sys
import unittest
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PYPROJECT = ROOT / "pyproject.toml"
MIGRATIONS = ROOT / "migrations"
LEGACY_DOCS = ROOT / "docs" / "legacy"
GITIGNORE = ROOT / ".gitignore"
TEXT_FILE_SUFFIXES = {
    ".py",
    ".md",
    ".sql",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".txt",
}


DOMAIN_RESOURCES = {
    "identity_access": ("auth", "dashboard", "users", "roles", "permissions", "endpoints"),
    "audit": ("logs",),
    "operations": ("jobs",),
}


def imported_modules(path):
    package = ".".join(path.relative_to(SRC).parts[:-1])
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            module = importlib.util.resolve_name(name, package) if node.level else name
            modules.add(module)
            modules.update(f"{module}.{alias.name}" for alias in node.names if alias.name != "*")
    return modules


class TestRefactorStructure(unittest.TestCase):
    def test_expected_top_level_directories_exist(self):
        expected = [
            "core",
            "infra",
            "domains",
            "middleware",
            "scripts/ops",
            "tests",
        ]
        for rel in expected:
            with self.subTest(path=rel):
                self.assertTrue((SRC / rel).exists(), rel)

    def test_expected_bounded_contexts_exist(self):
        expected = {
            "identity_access": ("services", "repositories", "models.py", "ports.py", "errors.py",
                                "policies.py", "audit.py", "cache.py", "security.py"),
            "audit": ("services/logs.py", "repositories/logs.py", "models.py", "ports.py", "records.py"),
            "operations": ("services/jobs.py", "ports.py", "jobs.py", "scheduler_gateway.py"),
        }
        for domain, paths in expected.items():
            with self.subTest(service_package=domain):
                self.assertTrue((SRC / "domains" / domain / "services").is_dir())
                self.assertFalse((SRC / "domains" / domain / "services.py").exists())
            for rel in (*paths, "controller/router.py"):
                with self.subTest(domain=domain, path=rel):
                    self.assertTrue((SRC / "domains" / domain / rel).exists())
        for domain in ("identity_access", "audit"):
            with self.subTest(repository_package=domain):
                self.assertTrue((SRC / "domains" / domain / "repositories").is_dir())
                self.assertFalse((SRC / "domains" / domain / "repositories.py").exists())

    def test_yaml_config_files_exist(self):
        expected = [
            "core/config/base.yaml",
            "core/config/sample.yaml",
            "core/config/schema.json",
        ]
        for rel in expected:
            with self.subTest(path=rel):
                self.assertTrue((SRC / rel).exists(), rel)

    def test_migration_scaffolding_exists(self):
        self.assertTrue(PYPROJECT.exists(), "pyproject.toml")
        self.assertTrue(MIGRATIONS.exists(), "migrations")
        self.assertTrue(LEGACY_DOCS.exists(), "docs/legacy")
        migration_app_dir = MIGRATIONS / "demo"
        self.assertTrue(migration_app_dir.exists(), "migration app directory")
        self.assertTrue(migration_app_dir.is_dir(), "migration app directory type")
        migration_files = [path for path in migration_app_dir.glob("*.py") if path.name != "__init__.py"]
        self.assertTrue(migration_files, "migration files")

    def test_gitignore_matches_current_project_layout(self):
        ignored_paths = {
            ".venv/bin/python",
            "venv/bin/python",
            ".vscode/settings.json",
            ".idea/workspace.xml",
            "src/__pycache__/app.cpython-312.pyc",
            "src/app.pyc",
            "src/app.pyo",
            "src/app.pyd",
            ".pytest_cache/README.md",
            ".mypy_cache/cache.json",
            ".ruff_cache/cache.bin",
            ".DS_Store",
            "src/.DS_Store",
            ".coverage",
            ".coverage.worker-1",
            "htmlcov/index.html",
            "build/lib/app.py",
            "dist/package.whl",
            "src/e_starter.egg-info/PKG-INFO",
            "app.log",
            "logs/events.json",
            "src/logs/events.json",
            "uploads/photo.png",
            "src/uploads/photo.png",
            "dump.rdb",
            ".env",
            ".env.local",
            "src/.env",
            "src/.env.production",
            "src/core/config/dev.yaml",
            "src/core/config/production.yaml",
            "src/core/config/local.yml",
        }
        kept_paths = {
            ".env.example",
            ".env.sample",
            ".env.template",
            "src/.env.example",
            "src/.env.sample",
            "src/.env.template",
            "src/core/config/base.yaml",
            "src/core/config/sample.yaml",
            "src/core/config/schema.json",
            "src/core/config/__init__.py",
            "src/app.py",
            "src/domains/audit/controller/logs/__init__.py",
            "src/domains/audit/controller/logs/api.py",
            "src/domains/audit/controller/logs/schemas.py",
            "src/domains/example/controller/logs/api.py",
            "src/domains/example/controller/uploads/api.py",
            "src/domains/example/controller/uploads/schemas.py",
            "src/tests/fixtures/config.yaml",
            "src/tests/fixtures/database.sqlite3",
            "migrations/demo/0_initial.py",
            "migrations/demo/schema.sql",
            "src/requirements.txt",
            "pyproject.toml",
            "poetry.lock",
            "uv.lock",
            "Pipfile.lock",
            "AGENTS.md",
            "README.md",
        }
        git = ["git", "-c", f"core.excludesFile={os.devnull}"]
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [*git, "init", "--quiet", "--template=", directory],
                check=True, capture_output=True, text=True, timeout=10,
            )
            (Path(directory) / ".gitignore").write_text(
                GITIGNORE.read_text(encoding="utf-8"), encoding="utf-8",
            )
            result = subprocess.run(
                [*git, "check-ignore", "--no-index", "--stdin", "-z"],
                input="\0".join(sorted(ignored_paths | kept_paths)) + "\0",
                cwd=directory, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            actual_ignored = set(result.stdout.split("\0")) - {""}
            self.assertEqual(actual_ignored, ignored_paths)

    def test_source_tree_contains_no_chinese_text(self):
        for root in [SRC, ROOT / "docs", ROOT / "README.md"]:
            if root.is_file():
                contents = root.read_text(encoding="utf-8")
                self.assertNotRegex(contents, r"[\u4e00-\u9fff]")
                continue

            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if "__pycache__" in path.parts or path.suffix.lower() not in TEXT_FILE_SUFFIXES:
                    continue
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    contents = path.read_text(encoding="utf-8")
                    self.assertNotRegex(contents, r"[\u4e00-\u9fff]")

    def test_source_modules_compile(self):
        for path in SRC.rglob("*.py"):
            with self.subTest(module=path.relative_to(SRC).as_posix()):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_legacy_context_directories_removed(self):
        for rel in ("domains/user", "domains/rbac", "domains/ops", "domains/audit/api", "domains/audit/schemas"):
            self.assertFalse((SRC / rel).exists(), rel)
        for domain in DOMAIN_RESOURCES:
            for layer in ("application", "domain", "infrastructure", "presentation"):
                with self.subTest(domain=domain, layer=layer):
                    self.assertFalse((SRC / "domains" / domain / layer).exists())

    def test_unused_shadowing_exception_module_is_removed(self):
        self.assertFalse((SRC / "core/exceptions.py").exists())

    def test_application_entrypoints_are_plain_functions(self):
        self.assertTrue((SRC / "app.py").is_file())
        self.assertFalse((SRC / "app").exists())
        expected = {
            "app.py": {"create_app", "create_http_app"},
            "main.py": {"start_http_server", "start_scheduler", "cli"},
        }
        for filename, names in expected.items():
            with self.subTest(module=filename):
                tree = ast.parse((SRC / filename).read_text(encoding="utf-8"))
                functions = {
                    node.name for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                self.assertTrue(names <= functions)
                self.assertFalse(any(isinstance(node, ast.ClassDef) for node in ast.walk(tree)))

    def test_domains_and_infrastructure_do_not_import_entrypoints(self):
        for root in (SRC / "domains", SRC / "infra"):
            for path in root.rglob("*.py"):
                with self.subTest(module=path.relative_to(SRC).as_posix()):
                    self.assertFalse({module.split(".")[0] for module in imported_modules(path)} & {"app", "main"})

    def test_domain_package_markers_have_no_imports_or_runtime_logic(self):
        for path in (SRC / "domains").rglob("__init__.py"):
            with self.subTest(module=path.relative_to(SRC).as_posix()):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                self.assertTrue(all(
                    isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    for node in tree.body
                ))

    def test_production_modules_do_not_reference_retired_domain_layers(self):
        for path in SRC.rglob("*.py"):
            if "tests" in path.relative_to(SRC).parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = imported_modules(path) | {
                node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and node.value.startswith(("domains.", "app.bootstrap"))
            }
            with self.subTest(module=path.relative_to(SRC).as_posix()):
                for name in names:
                    parts = name.split(".")
                    self.assertFalse(name.startswith("app.bootstrap"))
                    if len(parts) > 2 and parts[0] == "domains":
                        self.assertNotIn(parts[2], {"application", "domain", "infrastructure", "presentation"})

    def test_domain_module_import_graph_has_no_cycles(self):
        paths = {}
        for path in (SRC / "domains").rglob("*.py"):
            relative = path.relative_to(SRC).with_suffix("")
            parts = relative.parts[:-1] if path.name == "__init__.py" else relative.parts
            paths[".".join(parts)] = path
        graph = {name: imported_modules(path) & paths.keys() for name, path in paths.items()}
        visited = set()

        def visit(name, chain):
            self.assertNotIn(name, chain, " -> ".join((*chain, name)))
            if name in visited:
                return
            for dependency in sorted(graph[name]):
                visit(dependency, (*chain, name))
            visited.add(name)

        for name in sorted(graph):
            visit(name, ())

    def test_fresh_imports_do_not_construct_runtime_resources(self):
        modules = []
        for path in (SRC / "domains").rglob("*.py"):
            relative = path.relative_to(SRC).with_suffix("")
            parts = relative.parts[:-1] if path.name == "__init__.py" else relative.parts
            modules.append(".".join(parts))
        modules.extend(("app", "main", "scripts.ops.cli", "infra.database"))
        script = textwrap.dedent("""
            import importlib
            import json
            import sys
            from contextlib import ExitStack
            from unittest.mock import patch

            sys.path.insert(0, sys.argv[1])
            targets = (
                "tortoise.Tortoise.init",
                "tortoise.backends.base.client.BaseDBAsyncClient.__init__",
                "redis.asyncio.ConnectionPool.__init__",
                "infra.redis.RedisClient.__init__",
                "infra.scheduler.Scheduler.__init__",
                "sanic.Sanic.__init__",
            )
            with ExitStack() as stack:
                for target in targets:
                    stack.enter_context(patch(target, side_effect=AssertionError(target)))
                for module in json.loads(sys.argv[2]):
                    importlib.import_module(module)
        """)
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script, str(SRC),
                     json.dumps(sorted(set(modules), reverse=reverse))],
                    cwd=ROOT, text=True, capture_output=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_config_includes_sanic_worker_settings(self):
        import yaml

        sys.path.insert(0, str(SRC))
        try:
            from core.config import ConfigModel

            self.assertEqual(ConfigModel().sanic_workers, 1)
            for filename in ("base.yaml", "sample.yaml"):
                with self.subTest(config=filename):
                    values = yaml.safe_load((SRC / "core/config" / filename).read_text(encoding="utf-8"))
                    self.assertEqual(values["server"]["workers"], 1)
            schema = json.loads((SRC / "core/config/schema.json").read_text(encoding="utf-8"))
            self.assertEqual(schema["properties"]["server"]["properties"]["workers"]["minimum"], 1)
        finally:
            sys.path.pop(0)

    def test_request_handling_only_enriches_context_and_logs_safely(self):
        content = (SRC / "middleware/request_handling/request_handling.py").read_text(encoding="utf-8")
        support_content = (SRC / "domains/identity_access/controller/support.py").read_text(encoding="utf-8")
        rate_limit_content = (SRC / "infra/security/rate_limit.py").read_text(encoding="utf-8")
        jwt_content = (SRC / "infra/security/jwt.py").read_text(encoding="utf-8")

        self.assertIn("request.ctx.request_path", content)
        self.assertIn("def extract_request_payload", content)
        self.assertIn("def format_request_payload", content)
        self.assertNotIn("RequestException", content)
        self.assertNotIn("raise RequestException", content)
        self.assertIn("request.ctx.request_path", support_content)
        self.assertIn("request.ctx.request_path", rate_limit_content)
        self.assertIn("request.ctx.request_path", jwt_content)

    def test_pagination_returns_structured_page_result(self):
        content = (SRC / "core/pagination.py").read_text(encoding="utf-8")
        users_controller = (SRC / "domains/identity_access/controller/users/api.py").read_text(encoding="utf-8")
        roles_controller = (SRC / "domains/identity_access/controller/roles/api.py").read_text(encoding="utf-8")
        permissions_controller = (SRC / "domains/identity_access/controller/permissions/api.py").read_text(encoding="utf-8")
        endpoints_controller = (SRC / "domains/identity_access/controller/endpoints/api.py").read_text(encoding="utf-8")
        audit_repository = (SRC / "domains/audit/repositories/logs.py").read_text(encoding="utf-8")

        self.assertIn("class PageResult", content)
        self.assertIn("return PageResult(", content)
        self.assertIn("page_result = await self.user_service.list_users", users_controller)
        self.assertIn("page_result = await self.role_service.list_roles", roles_controller)
        self.assertIn("page_result = await self.permission_service.list_permissions", permissions_controller)
        self.assertIn("page_result = await self.endpoint_service.list_endpoints", endpoints_controller)
        self.assertIn("page_result = await paginate_query", audit_repository)

    def test_services_depend_on_ports_not_concrete_adapters(self):
        paths = list(SRC.glob("domains/*/services/*.py"))
        self.assertGreater(len(paths), 2)
        for path in paths:
            with self.subTest(module=path.relative_to(SRC).as_posix()):
                modules = imported_modules(path)
                if path.name != "__init__.py":
                    self.assertTrue(any("ports" in module.split(".") for module in modules))
                for module in modules:
                    parts = module.split(".")
                    self.assertNotIn(parts[0], {"app", "main", "infra", "sanic", "sanic_ext", "tortoise", "redis"})
                    if parts[0] == "domains":
                        self.assertFalse(set(parts[2:]) & {
                            "models", "repositories", "cache", "security", "scheduler_gateway", "controller",
                        })

    def test_scheduler_uses_current_infra_paths(self):
        content = (SRC / "infra/scheduler/base.py").read_text(encoding="utf-8")
        self.assertNotIn("utils.redis_util", content)
        self.assertNotIn("from scheduler import", content)
        self.assertIn("class SchedulerRegistry", content)
        self.assertIn("scheduler_registry = SchedulerRegistry()", content)
        self.assertIn("from infra.redis import RedisClient, RedisLock", content)
        self.assertIn('importlib.import_module(f"{package_name}.{module_dir.name}.task")', content)
        self.assertNotRegex(content, re.compile(r"^\s*_instance\s*=", re.MULTILINE))
        self.assertNotRegex(content, re.compile(r"^\s*def __new__\(", re.MULTILINE))

    def test_scheduler_package_exports_canonical_base_module(self):
        content = (SRC / "infra/scheduler/__init__.py").read_text(encoding="utf-8")
        self.assertIn("from .base import Scheduler", content)
        self.assertIn("add_task", content)
        self.assertIn("add_interval_job", content)

    def test_scheduler_tasks_register_through_registry_decorators(self):
        job_content = (SRC / "infra/scheduler/jobs/update_endpoint/task.py").read_text(encoding="utf-8")
        task_content = (SRC / "infra/scheduler/tasks/demo/task.py").read_text(encoding="utf-8")

        self.assertIn("from infra.scheduler import add_interval_job", job_content)
        self.assertNotIn("Scheduler()", job_content)
        self.assertIn("@add_interval_job(", job_content)
        self.assertIn("from infra.scheduler import add_task", task_content)
        self.assertNotIn("Scheduler()", task_content)
        self.assertIn("@add_task(", task_content)

    def test_operations_context_uses_domain_job_contracts(self):
        application_content = (SRC / "domains/operations/services/jobs.py").read_text(encoding="utf-8")
        ports_content = (SRC / "domains/operations/ports.py").read_text(encoding="utf-8")
        domain_content = (SRC / "domains/operations/jobs.py").read_text(encoding="utf-8")
        handler_content = (SRC / "domains/operations/controller/jobs/api.py").read_text(encoding="utf-8")
        gateway_content = (SRC / "domains/operations/scheduler_gateway.py").read_text(encoding="utf-8")

        self.assertIn("SchedulerJob", application_content)
        self.assertIn("SchedulerJobUpdate", application_content)
        self.assertIn("class SchedulerJobsPort", ports_content)
        self.assertIn("class SchedulerJob", domain_content)
        self.assertIn("class SchedulerJobUpdate", domain_content)
        self.assertNotIn("from ..infrastructure", application_content)
        self.assertNotIn("def set_job", gateway_content)

    def test_audit_context_uses_domain_log_contracts(self):
        ports_content = (SRC / "domains/audit/ports.py").read_text(encoding="utf-8")
        domain_content = (SRC / "domains/audit/records.py").read_text(encoding="utf-8")
        application_content = (SRC / "domains/audit/services/logs.py").read_text(encoding="utf-8")
        repository_content = (SRC / "domains/audit/repositories/logs.py").read_text(encoding="utf-8")
        handler_content = (SRC / "domains/audit/controller/logs/api.py").read_text(encoding="utf-8")

        self.assertIn("class AuditLogStore", ports_content)
        self.assertIn("class AuditLogRecord", domain_content)
        self.assertIn("class AuditLogPage", domain_content)
        self.assertIn("AuditLogRecord", application_content)
        self.assertNotIn("from ..infrastructure", application_content)
        self.assertIn("AuditLogPage", repository_content)
        self.assertNotIn("AuditLogService()", handler_content)

    def test_routing_requires_explicit_jwt_auth_when_authorizing(self):
        sys.path.insert(0, str(SRC))
        try:
            try:
                from infra.web.routing import build_route_handler
            except ModuleNotFoundError as exc:
                self.skipTest(f"Web dependencies are unavailable: {exc}")

            async def handler(request):
                return None

            with self.assertRaisesRegex(ValueError, "jwt_auth is required"):
                build_route_handler(handler, authorize=True)
        finally:
            sys.path.pop(0)

    def test_http_layers_use_controllers_instead_of_route_local_closures(self):
        expected = {
            "domains/identity_access/controller/auth/api.py": "class UserAuthController",
            "domains/identity_access/controller/dashboard/api.py": "class DashboardController",
            "domains/identity_access/controller/users/api.py": "class UserAdminController",
            "domains/identity_access/controller/roles/api.py": "class RoleAdminController",
            "domains/identity_access/controller/permissions/api.py": "class PermissionAdminController",
            "domains/identity_access/controller/endpoints/api.py": "class EndpointAdminController",
            "domains/audit/controller/logs/api.py": "class AuditLogController",
            "domains/operations/controller/jobs/api.py": "class SchedulerJobsController",
        }
        for rel, controller_name in expected.items():
            with self.subTest(path=rel):
                content = (SRC / rel).read_text(encoding="utf-8")
                self.assertIn(controller_name, content)
                self.assertNotIn("async def register_routes", content)

    def test_controller_dependencies_use_concrete_service_types(self):
        cases = (
            ("audit", "logs", "AuditLogController", "audit_service", "services.logs", "AuditLogService"),
            ("operations", "jobs", "SchedulerJobsController", "job_service", "services.jobs", "SchedulerJobService"),
            ("identity_access", "auth", "UserAuthController", "auth_service", "services.auth", "AuthService"),
            ("identity_access", "dashboard", "DashboardController", "dashboard_service",
             "services.dashboard", "DashboardService"),
            ("identity_access", "users", "UserAdminController", "user_service", "services.users", "UserAdminService"),
            ("identity_access", "roles", "RoleAdminController", "role_service", "services.roles", "RoleAdminService"),
            ("identity_access", "permissions", "PermissionAdminController", "permission_service",
             "services.permissions", "PermissionAdminService"),
            ("identity_access", "endpoints", "EndpointAdminController", "endpoint_service",
             "services.endpoints", "EndpointAdminService"),
        )
        sys.path.insert(0, str(SRC))
        try:
            for domain, resource, controller_name, field, service_module, service_name in cases:
                with self.subTest(controller=controller_name):
                    module = importlib.import_module(f"domains.{domain}.controller.{resource}.api")
                    controller = getattr(module, controller_name)
                    service = getattr(importlib.import_module(f"domains.{domain}.{service_module}"), service_name)
                    self.assertIs(get_type_hints(controller)[field], service)
                    self.assertIs(get_type_hints(controller.__init__)[field], service)
        finally:
            sys.path.pop(0)

    def test_controller_resources_keep_api_and_schemas_together(self):
        for domain, resources in DOMAIN_RESOURCES.items():
            controller = SRC / "domains" / domain / "controller"
            actual = {path.name for path in controller.iterdir()
                      if path.is_dir() and path.name != "__pycache__"}
            self.assertEqual(actual, set(resources))
            for resource in resources:
                with self.subTest(domain=domain, resource=resource):
                    self.assertTrue((controller / resource / "api.py").is_file())
                    self.assertTrue((controller / resource / "schemas.py").is_file())

    def test_domain_routers_register_resources_with_explicit_dependencies(self):
        for domain, resources in DOMAIN_RESOURCES.items():
            router = SRC / "domains" / domain / "controller/router.py"
            modules = imported_modules(router)
            for resource in resources:
                self.assertIn(f"domains.{domain}.controller.{resource}.api", modules)
            paths = [router, *(router.parent / resource / "api.py" for resource in resources)]
            for path in paths:
                with self.subTest(module=path.relative_to(SRC).as_posix()):
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                    register = next(node for node in tree.body
                                    if isinstance(node, ast.FunctionDef) and node.name == "register_routes")
                    self.assertIsNone(register.args.vararg)
                    self.assertIsNone(register.args.kwarg)
                    self.assertTrue(register.args.kwonlyargs)
                    names = {arg.arg for arg in (*register.args.args, *register.args.kwonlyargs)}
                    self.assertFalse(names & {"bootstrap", "container", "context", "runtime", "services"})
                    for node in ast.walk(register):
                        if isinstance(node, ast.Call):
                            self.assertTrue(all(keyword.arg is not None for keyword in node.keywords))

    def test_http_schemas_use_method_resource_and_parameter_location(self):
        sys.path.insert(0, str(SRC))
        try:
            from pydantic import BaseModel
            from core.api_schema import Response

            names = {}
            for path in [*SRC.glob("domains/*/controller/*/schemas.py"), *SRC.glob("domains/*/controller/common.py")]:
                if path.name == "__init__.py":
                    continue
                module_name = ".".join(path.relative_to(SRC).with_suffix("").parts)
                module = importlib.import_module(module_name)
                for name, model in vars(module).items():
                    if not isinstance(model, type) or not issubclass(model, BaseModel):
                        continue
                    if model.__module__ != module_name:
                        continue
                    with self.subTest(model=name):
                        self.assertIs(names.setdefault(name, model), model, "OpenAPI name collision")
                        self.assertFalse(issubclass(model, Response), "Reuse the shared response envelope")
            self.assertTrue(names)
        finally:
            sys.path.pop(0)

        input_count = 0
        for path in SRC.glob("domains/*/controller/*/api.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                    continue
                if node.func.id != "add_route":
                    continue
                arguments = {keyword.arg: keyword.value for keyword in node.keywords}
                method = ast.literal_eval(arguments["methods"])[0].title()
                for location, suffix in (("query", "Query"), ("json", "Body")):
                    if location not in arguments:
                        continue
                    model = arguments[location]
                    with self.subTest(path=path, location=location):
                        self.assertIsInstance(model, ast.Attribute)
                        self.assertRegex(model.attr, rf"^{method}[A-Z][A-Za-z0-9]*{suffix}$")
                    input_count += 1
        self.assertGreater(input_count, 0)

    def test_http_controller_methods_use_action_names_not_route_names(self):
        http_files = [
            "domains/identity_access/controller/auth/api.py",
            "domains/identity_access/controller/dashboard/api.py",
            "domains/identity_access/controller/users/api.py",
            "domains/identity_access/controller/roles/api.py",
            "domains/identity_access/controller/permissions/api.py",
            "domains/identity_access/controller/endpoints/api.py",
            "domains/audit/controller/logs/api.py",
            "domains/operations/controller/jobs/api.py",
        ]
        forbidden_patterns = [
            r"async def admin_",
            r"async def user_",
            r"\binvalid_response\(",
        ]
        for rel in http_files:
            with self.subTest(path=rel):
                content = (SRC / rel).read_text(encoding="utf-8")
                for pattern in forbidden_patterns:
                    self.assertNotRegex(content, pattern)

    def test_presentation_helpers_centralize_schema_mapping_and_responses(self):
        core_http_content = (SRC / "core/http.py").read_text(encoding="utf-8")
        support_content = (SRC / "domains/identity_access/controller/support.py").read_text(encoding="utf-8")
        users_controller_content = (SRC / "domains/identity_access/controller/users/api.py").read_text(
            encoding="utf-8"
        )
        auth_controller_content = (SRC / "domains/identity_access/controller/auth/api.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("def schema_response", core_http_content)
        self.assertIn("def schema_from", support_content)
        self.assertIn("def schema_list_from", support_content)
        self.assertIn("def invalid_arguments_response", support_content)
        self.assertNotIn("def args_invalid_response", support_content)
        self.assertNotIn("from core.http import http_response", users_controller_content)
        self.assertNotIn("from core.http import http_response", auth_controller_content)
        self.assertNotIn("args_invalid_response", users_controller_content)

    def test_invalid_arguments_response_preserves_http_and_business_error(self):
        sys.path.insert(0, str(SRC))
        try:
            from core.api_schema import ArgsInvalidResponse
            from domains.identity_access.controller.support import invalid_arguments_response

            response = invalid_arguments_response(ArgsInvalidResponse)
            self.assertEqual(response.status, 400)
            self.assertEqual(json.loads(response.body), {
                "code": -1002,
                "msg": "Invalid or missing arguments",
                "results": None,
            })
        finally:
            sys.path.pop(0)

    def test_crud_inputs_use_explicit_typed_parameters(self):
        self.assertFalse((SRC / "domains/identity_access/domain/selectors.py").exists())
        self.assertFalse((SRC / "domains/identity_access/application/contracts.py").exists())

        paths = []
        for resource in ("users", "roles", "permissions", "endpoints"):
            paths.append((SRC / f"domains/identity_access/services/{resource}.py", None))
            paths.append((SRC / f"domains/identity_access/repositories/{resource}.py",
                          {"find", "list", "delete"}))
        paths.extend([
            (SRC / "domains/identity_access/ports.py", {"find", "list", "delete"}),
            (SRC / "domains/audit/services/logs.py", {"list_logs"}),
            (SRC / "domains/audit/ports.py", {"list_logs"}),
            (SRC / "domains/audit/repositories/logs.py", {"list_logs"}),
            (SRC / "domains/operations/services/jobs.py", {"update_job"}),
        ])
        for path, methods in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.AsyncFunctionDef):
                    continue
                if methods is not None and node.name not in methods:
                    continue
                with self.subTest(path=path, method=node.name):
                    self.assertEqual([arg.arg for arg in node.args.args], ["self"])
                    self.assertFalse(node.args.posonlyargs)
                    self.assertIsNone(node.args.vararg)
                    self.assertIsNone(node.args.kwarg)
                    self.assertTrue(node.args.kwonlyargs)
                    for argument in node.args.kwonlyargs:
                        self.assertIsNotNone(argument.annotation, argument.arg)

    def test_endpoint_sync_job_uses_application_service_instead_of_orm(self):
        content = (SRC / "infra/scheduler/jobs/update_endpoint/task.py").read_text(encoding="utf-8")
        self.assertIn("EndpointRegistrySyncService", content)
        self.assertIn("SanicRouteCatalog", content)
        self.assertNotIn("domains.identity_access.models", content)
        self.assertNotIn("import sanic", content)
        self.assertNotIn("Endpoint.create", content)

    def test_config_loader_uses_yaml(self):
        content = (SRC / "core/config/__init__.py").read_text(encoding="utf-8")
        schema = json.loads((SRC / "core/config/schema.json").read_text(encoding="utf-8"))
        self.assertIn("yaml.safe_load", content)
        expected_sections = {
            "app": {"name", "debug", "timezone"},
            "server": {"host", "port", "workers", "forwarded_secret", "cors_domains"},
            "paths": {"relative", "uploads", "logs", "migrations"},
            "jwt": {"secret_key", "exp_time"},
            "mysql": {"host", "port", "username", "password", "database"},
            "redis": {"url"},
            "tools": {"pip"},
        }
        self.assertEqual(set(schema["properties"]), set(expected_sections))
        self.assertFalse(schema["additionalProperties"])
        for name, fields in expected_sections.items():
            with self.subTest(section=name):
                section = schema["properties"][name]
                self.assertEqual(section["type"], "object")
                self.assertEqual(set(section["properties"]), fields)
                self.assertFalse(section["additionalProperties"])

        sys.path.insert(0, str(SRC))
        try:
            from dataclasses import is_dataclass
            from core.config import Config, ConfigModel, load_config

            self.assertTrue(is_dataclass(ConfigModel))
            self.assertTrue(callable(load_config))
            self.assertTrue(callable(ConfigModel.apply_runtime_paths))
            self.assertIsNot(Config(), Config())
        finally:
            sys.path.pop(0)

    def test_yaml_config_files_reference_schema(self):
        for rel in ["core/config/base.yaml", "core/config/sample.yaml"]:
            with self.subTest(path=rel):
                first_line = (SRC / rel).read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first_line, "# yaml-language-server: $schema=./schema.json")

    def test_database_uses_explicit_orm_metadata(self):
        database_content = (SRC / "infra/database.py").read_text(encoding="utf-8")
        models_content = (SRC / "domains/identity_access/models.py").read_text(encoding="utf-8")
        audit_models_content = (SRC / "domains/audit/models.py").read_text(encoding="utf-8")

        self.assertIn("ORM_MODEL_MODULES", database_content)
        self.assertIn("cfg.app", database_content)
        self.assertIn("build_tortoise_orm_config", database_content)
        self.assertIn("load_config().app", models_content)
        self.assertIn("load_config().app", audit_models_content)
        self.assertIn('os.environ.get("DB_AUTO_SCHEMA", "0")', database_content)
        self.assertIn("generate_schemas=False", database_content)
        self.assertNotIn("demo.", models_content)
        self.assertNotIn("demo.", audit_models_content)
        self.assertNotRegex(models_content, r"(?<!_)pk=True")
        self.assertNotRegex(models_content, r"(?<!db_)index=True")
        self.assertNotRegex(audit_models_content, r"(?<!_)pk=True")
        self.assertNotRegex(audit_models_content, r"(?<!db_)index=True")
        self.assertIn("password = fields.CharField(max_length=255", models_content)

    def test_project_has_aerich_config(self):
        import tomllib

        config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["aerich"]
        self.assertEqual(config["tortoise_orm"], "infra.database.TORTOISE_ORM")
        self.assertEqual(config["location"], "./migrations")
        self.assertEqual(config["src"], "./src")

    def test_http_response_uses_results_key(self):
        try:
            import yaml  # noqa: F401
            import sanic  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("YAML or Sanic dependencies are not installed in the current interpreter")

        sys.path.insert(0, str(SRC))
        try:
            from core.http import http_response

            payload = json.loads(http_response(0, "ok", results={"id": 1}).body)
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["msg"], "ok")
            self.assertEqual(payload["results"], {"id": 1})
            self.assertNotIn("result", payload)
            with self.assertRaises(TypeError):
                http_response(0, "ok", result=[1, 2])
        finally:
            sys.path.pop(0)

    def test_rate_limit_uses_business_error_code_and_http_429(self):
        content = (SRC / "infra/security/rate_limit.py").read_text(encoding="utf-8")
        self.assertIn("TooManyRequestsError.code", content)
        self.assertIn("TooManyRequestsError.msg", content)
        self.assertNotIn('http_response(429, "Too many requests")', content)
        self.assertNotIn("RedisConn = RedisClient", content)
        self.assertIn("get_rate_limit_redis", content)

    def test_redis_client_has_no_debug_side_effects(self):
        content = (SRC / "infra/redis/client.py").read_text(encoding="utf-8")
        self.assertNotIn("print(", content)
        self.assertNotIn('if __name__ == "__main__"', content)
        self.assertIn("logger.exception", content)
        self.assertNotRegex(content, re.compile(r"^\s*_instance\s*=", re.MULTILINE))
        self.assertNotRegex(content, re.compile(r"^\s*def __new__\(", re.MULTILINE))

    def test_jwt_auth_is_not_a_singleton(self):
        content = (SRC / "infra/security/jwt.py").read_text(encoding="utf-8")
        self.assertIn("class JwtAuth", content)
        self.assertIn("def __init__", content)
        self.assertNotRegex(content, re.compile(r"^\s*_instance\s*=", re.MULTILINE))
        self.assertNotRegex(content, re.compile(r"^\s*def __new__\(", re.MULTILINE))

    def test_password_security_supports_verify_and_rehash(self):
        ports_content = (SRC / "domains/identity_access/ports.py").read_text(encoding="utf-8")
        security_content = (SRC / "domains/identity_access/security.py").read_text(encoding="utf-8")
        password_content = (SRC / "infra/security/passwords.py").read_text(encoding="utf-8")
        auth_content = (SRC / "domains/identity_access/services/auth.py").read_text(encoding="utf-8")

        self.assertIn("def verify_password", ports_content)
        self.assertIn("def needs_rehash", ports_content)
        self.assertIn("def verify_password", security_content)
        self.assertIn("def needs_rehash", security_content)
        self.assertIn("PasswordHasher", password_content)
        self.assertIn("def verify_password", password_content)
        self.assertIn("def needs_rehash", password_content)
        self.assertIn("self.credentials.verify_password", auth_content)
        self.assertIn("self.credentials.needs_rehash", auth_content)
        self.assertNotIn("hashed_password = self.credentials.hash_password(password)", auth_content)

    def test_compatibility_layers_are_removed(self):
        removed_files = [
            "domains/audit/application/services.py",
            "domains/identity_access/application/services.py",
            "domains/identity_access/infrastructure/repositories.py",
            "domains/operations/application/services.py",
            "infra/scheduler/main.py",
        ]
        for rel in removed_files:
            with self.subTest(path=rel):
                self.assertFalse((SRC / rel).exists(), rel)

        responses_content = (SRC / "core/responses.py").read_text(encoding="utf-8")
        api_schema_content = (SRC / "core/api_schema.py").read_text(encoding="utf-8")
        constants_content = (SRC / "core/constants.py").read_text(encoding="utf-8")
        identity_auth_schema_content = (SRC / "domains/identity_access/controller/auth/schemas.py").read_text(encoding="utf-8")
        audit_logs_content = (SRC / "domains/audit/services/logs.py").read_text(encoding="utf-8")
        operations_jobs_content = (SRC / "domains/operations/services/jobs.py").read_text(encoding="utf-8")
        verification_init_content = (SRC / "infra/verification/__init__.py").read_text(encoding="utf-8")

        self.assertNotRegex(responses_content, re.compile(r"^TimeoutError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^ArgsInvalidError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^TokenError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^RateLimitError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^AuthorizedError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^UserExistError\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^AccountOrPasswordInvalid\s*=", re.MULTILINE))
        self.assertNotRegex(responses_content, re.compile(r"^Successfully\s*=", re.MULTILINE))
        self.assertNotIn("TokenExpiedResponse", api_schema_content)
        self.assertNotIn("MIDIUM", constants_content)
        self.assertNotIn("EMAIL_VERCODE", constants_content)
        self.assertNotIn("WEB3_VERCODE", constants_content)
        self.assertNotIn("AccountOrPasswordInvalidResponse", identity_auth_schema_content)
        self.assertNotIn("UserExistResponse", identity_auth_schema_content)
        self.assertNotIn("AuditLogApplicationService", audit_logs_content)
        self.assertNotIn("SchedulerJobApplicationService", operations_jobs_content)
        self.assertNotIn("EmailAuth", verification_init_content)
        self.assertNotIn("Web3Auth", verification_init_content)
        self.assertNotIn("get_base64_captcha", verification_init_content)
        self.assertNotIn("get_captcha", verification_init_content)

    def test_core_submodules_do_not_eagerly_import_config(self):
        sys.path.insert(0, str(SRC))
        try:
            from core.responses import InvalidArgumentsError, TokenExpiredError

            self.assertEqual(InvalidArgumentsError.code, -1002)
            self.assertEqual(InvalidArgumentsError.msg, "Invalid or missing arguments")
            self.assertEqual(TokenExpiredError.msg, "Token expired")
        finally:
            sys.path.pop(0)

    def test_config_can_load_yaml_when_dependency_is_installed(self):
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("PyYAML is not installed in the current interpreter")

        sys.path.insert(0, str(SRC))
        try:
            from core.config import load_config

            config = load_config()
            self.assertTrue(config.app)
            self.assertEqual(config.sanic_port, 8000)
            self.assertEqual(config.jwt_exp_time, 86400)
            self.assertEqual(config.cors_domains[0], "localhost.com")
        finally:
            sys.path.pop(0)

    def test_experimental_web3_verifier_is_removed_from_production_tree(self):
        self.assertFalse((SRC / "infra/verification/web3_auth.py").exists())
        init_content = (SRC / "infra/verification/__init__.py").read_text(encoding="utf-8")
        constants_content = (SRC / "core/constants.py").read_text(encoding="utf-8")
        self.assertNotIn("Web3Verifier", init_content)
        self.assertNotIn("WEB3_VERIFICATION_CODE_KEY", constants_content)

    def test_verification_layer_uses_capability_focused_modules(self):
        init_content = (SRC / "infra/verification/__init__.py").read_text(encoding="utf-8")
        email_content = (SRC / "infra/verification/email.py").read_text(encoding="utf-8")
        captcha_content = (SRC / "infra/verification/captcha.py").read_text(encoding="utf-8")

        self.assertTrue((SRC / "infra/verification/email.py").exists())
        self.assertTrue((SRC / "infra/verification/captcha.py").exists())
        self.assertFalse((SRC / "infra/verification/email_auth.py").exists())
        self.assertFalse((SRC / "infra/verification/image_captcha.py").exists())
        self.assertIn("EmailCodeVerifier", init_content)
        self.assertIn("CaptchaChallenge", init_content)
        self.assertIn("ImageCaptchaService", init_content)
        self.assertIn("class EmailCodeVerifier", email_content)
        self.assertIn("def _normalize_email", email_content)
        self.assertIn("class CaptchaChallenge", captcha_content)
        self.assertIn("class ImageCaptchaService", captcha_content)
        self.assertIn("def create_challenge", captcha_content)
        self.assertNotIn("class EmailVerifier", email_content)
        self.assertNotIn("def generate_captcha_text", captcha_content)
        self.assertNotIn("def encode_captcha_base64", captcha_content)

    def test_migration_config_can_be_imported_when_orm_dependency_is_installed(self):
        try:
            import yaml  # noqa: F401
            import tortoise  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("YAML or Tortoise ORM dependencies are not installed in the current interpreter")

        sys.path.insert(0, str(SRC))
        try:
            from infra.database import TORTOISE_ORM
            from core.config import load_config

            app_name = load_config().app

            self.assertIn("connections", TORTOISE_ORM)
            self.assertIn("apps", TORTOISE_ORM)
            self.assertIn(app_name, TORTOISE_ORM["apps"])
            self.assertIn("aerich.models", TORTOISE_ORM["apps"][app_name]["models"])
        finally:
            sys.path.pop(0)

    def test_cli_uses_aerich_instead_of_generate_schemas(self):
        content = (SRC / "scripts/ops/cli.py").read_text(encoding="utf-8")
        self.assertIn("run_aerich_command", content)
        self.assertIn('"aerich"', content)
        self.assertIn("return asyncio.run(runner())", content)
        self.assertIn("asyncio.run(check_database_connection())", content)
        self.assertIn("capture_output=True", content)
        self.assertNotIn("Tortoise.generate_schemas", content)
        self.assertNotIn("from tortoise import Tortoise, run_async", content)
        self.assertNotIn("run_async(", content)
        self.assertIn("def get_migration_app_dir", content)
        self.assertIn("migration_app_dir = get_migration_app_dir()", content)
        self.assertIn("for path in migration_app_dir.iterdir()", content)
        self.assertNotIn("domains.identity_access.models", content)
        self.assertNotIn("from infra.security import generate_openid", content)
        self.assertNotIn('@click.option("--pre"', content)
        self.assertNotIn('command.extend(["--pre", pre])', content)
        self.assertIn('cli.command("seed_identity_access")', content)
        self.assertIn('cli.command("migration_init_migrations")', content)
        self.assertIn('cli.command("migration_doctor")', content)

    def test_legacy_schema_dump_is_removed(self):
        self.assertFalse((SRC / "scripts/ops/demo.sql").exists())
        self.assertFalse((ROOT / "docs" / "legacy" / "sql" / "demo.sql").exists())


if __name__ == "__main__":
    unittest.main()
