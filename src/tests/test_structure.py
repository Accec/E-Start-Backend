import py_compile
import re
import sys
import unittest
import json
from pathlib import Path


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


class TestRefactorStructure(unittest.TestCase):
    def test_expected_top_level_directories_exist(self):
        expected = [
            "app/bootstrap",
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
        expected = [
            "domains/identity_access/application",
            "domains/identity_access/application/use_cases",
            "domains/identity_access/domain",
            "domains/identity_access/infrastructure",
            "domains/identity_access/infrastructure/repos",
            "domains/identity_access/presentation/http",
            "domains/identity_access/presentation/schemas",
            "domains/audit/application",
            "domains/audit/application/ports.py",
            "domains/audit/domain",
            "domains/audit/infrastructure",
            "domains/audit/presentation/http",
            "domains/audit/presentation/schemas",
            "domains/operations/application",
            "domains/operations/application/ports.py",
            "domains/operations/domain",
            "domains/operations/infrastructure",
            "domains/operations/presentation/http",
            "domains/operations/presentation/schemas",
        ]
        for rel in expected:
            with self.subTest(path=rel):
                self.assertTrue((SRC / rel).exists(), rel)

    def test_yaml_config_files_exist(self):
        expected = [
            "core/config/base.yaml",
            "core/config/sample.yaml",
            "core/config/dev.yaml",
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
        content = GITIGNORE.read_text(encoding="utf-8")
        self.assertIn(".venv/", content)
        self.assertIn("__pycache__/", content)
        self.assertIn("logs/", content)
        self.assertIn("uploads/", content)
        self.assertNotIn("src/config/*", content)
        self.assertNotIn("!src/config/sample.py", content)
        self.assertNotIn("src/logs/", content)

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

    def test_key_modules_compile(self):
        key_modules = [
            "main.py",
            "app/bootstrap/application.py",
            "app/bootstrap/audit.py",
            "app/bootstrap/container.py",
            "app/bootstrap/routes.py",
            "app/bootstrap/routing.py",
            "app/bootstrap/runtime.py",
            "app/bootstrap/database.py",
            "app/bootstrap/migrations.py",
            "app/bootstrap/identity_access.py",
            "app/bootstrap/operations.py",
            "core/api_schema.py",
            "core/config/__init__.py",
            "core/http.py",
            "core/pagination.py",
            "core/persistence.py",
            "infra/security/jwt.py",
            "infra/security/passwords.py",
            "infra/scheduler/base.py",
            "infra/scheduler/jobs/update_endpoint/task.py",
            "infra/scheduler/tasks/demo/task.py",
            "infra/web/health.py",
            "infra/web/route_catalog.py",
            "infra/verification/email.py",
            "infra/verification/captcha.py",
            "domains/identity_access/application/authorization.py",
            "domains/identity_access/application/contracts.py",
            "domains/identity_access/application/ports.py",
            "domains/identity_access/application/use_cases/bootstrap.py",
            "domains/identity_access/application/use_cases/auth.py",
            "domains/identity_access/application/use_cases/dashboard.py",
            "domains/identity_access/application/use_cases/endpoint_registry.py",
            "domains/identity_access/application/use_cases/users.py",
            "domains/identity_access/application/use_cases/roles.py",
            "domains/identity_access/application/use_cases/permissions.py",
            "domains/identity_access/application/use_cases/endpoints.py",
            "domains/identity_access/domain/request_meta.py",
            "domains/identity_access/domain/selectors.py",
            "domains/identity_access/infrastructure/models.py",
            "domains/identity_access/infrastructure/repos/users.py",
            "domains/identity_access/infrastructure/repos/roles.py",
            "domains/identity_access/infrastructure/repos/permissions.py",
            "domains/identity_access/infrastructure/repos/endpoints.py",
            "domains/identity_access/infrastructure/security.py",
            "domains/identity_access/infrastructure/cache.py",
            "domains/identity_access/presentation/http/support.py",
            "domains/identity_access/presentation/http/user/auth.py",
            "domains/identity_access/presentation/http/user/dashboard.py",
            "domains/identity_access/presentation/http/admin/users.py",
            "domains/identity_access/presentation/http/admin/roles.py",
            "domains/identity_access/presentation/http/admin/permissions.py",
            "domains/identity_access/presentation/http/admin/endpoints.py",
            "domains/audit/application/logs.py",
            "domains/audit/application/ports.py",
            "domains/audit/domain/logs.py",
            "domains/audit/infrastructure/models.py",
            "domains/audit/presentation/http/admin/logs.py",
            "domains/operations/application/jobs.py",
            "domains/operations/application/ports.py",
            "domains/operations/domain/jobs.py",
            "domains/operations/presentation/http/admin/jobs.py",
            "middleware/request_handling/request_handling.py",
            "scripts/ops/cli.py",
            "tests/test_health_checks.py",
            "tests/test_logging_configuration.py",
            "tests/test_pagination.py",
            "tests/test_password_security.py",
            "tests/test_request_handling.py",
            "tests/test_runtime_multiworker.py",
        ]
        for rel in key_modules:
            with self.subTest(module=rel):
                py_compile.compile(str(SRC / rel), doraise=True)

    def test_legacy_context_directories_removed(self):
        legacy_paths = [
            "domains/user",
            "domains/rbac",
            "domains/ops",
            "domains/audit/api",
            "domains/audit/schemas",
            "domains/audit/models.py",
        ]
        for rel in legacy_paths:
            with self.subTest(path=rel):
                self.assertFalse((SRC / rel).exists(), rel)

    def test_unused_shadowing_exception_module_is_removed(self):
        self.assertFalse((SRC / "core/exceptions.py").exists())

    def test_main_uses_new_layers(self):
        content = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn('if args.command == "server"', content)
        self.assertIn('if args.command == "scheduler"', content)
        self.assertIn("from app.bootstrap import start_http_server", content)
        self.assertIn("from app.bootstrap import start_scheduler", content)
        self.assertIn("start_http_server", content)
        self.assertIn("start_scheduler", content)
        self.assertIn("from scripts.ops import cli", content)
        self.assertNotIn("asyncio.run(start_http_server())", content)
        self.assertNotIn("from app.bootstrap import start_http_server, start_scheduler", content)
        self.assertNotIn("from core.config import Config", content)
        self.assertNotIn("from infra.scheduler import Scheduler", content)
        self.assertNotIn("from infra.security import JwtAuth", content)

    def test_bootstrap_package_uses_lazy_exports(self):
        content = (SRC / "app/bootstrap/__init__.py").read_text(encoding="utf-8")
        self.assertIn("from importlib import import_module", content)
        self.assertIn("def __getattr__", content)
        self.assertIn("_EXPORT_MAP", content)
        self.assertNotIn("from .routes import get_blueprints", content)
        self.assertNotIn("from .runtime import ApplicationRuntime", content)
        self.assertNotIn("from .container import ApplicationBootstrap", content)

    def test_runtime_bootstrap_owns_server_and_scheduler_wiring(self):
        content = (SRC / "app/bootstrap/runtime.py").read_text(encoding="utf-8")
        container_content = (SRC / "app/bootstrap/container.py").read_text(encoding="utf-8")
        application_content = (SRC / "app/bootstrap/application.py").read_text(encoding="utf-8")
        self.assertIn("class ApplicationRuntime", content)
        self.assertIn("bootstrap: ApplicationBootstrap", content)
        self.assertIn("def build_runtime", content)
        self.assertIn("def build_http_server", content)
        self.assertIn("def build_scheduler", content)
        self.assertIn("def resolve_bootstrap", content)
        self.assertIn("def setup_logging", content)
        self.assertIn("async def init_scheduler_application", content)
        self.assertIn("async def start_single_worker_http_server", content)
        self.assertIn("def start_multi_worker_http_server", content)
        self.assertIn("def start_http_server", content)
        self.assertIn("async def start_scheduler", content)
        self.assertIn("def build_http_server_from_config", content)
        self.assertIn("request_handling", content)
        self.assertIn("get_blueprints", content)
        self.assertIn("build_bootstrap", content)
        self.assertIn("self.bootstrap = build_bootstrap(self.config)", content)
        self.assertIn("return self.resolve_bootstrap().operations.scheduler", content)
        self.assertIn("if self.config.sanic_workers == 1", content)
        self.assertIn("AppLoader(factory=server_factory)", content)
        self.assertIn("Sanic.serve(primary=primary", content)
        self.assertNotIn("def bind_http_server_lifecycle", content)
        self.assertNotIn("def should_embed_scheduler", content)
        self.assertNotIn("scheduler.run_by_async()", content)
        self.assertNotIn("app.add_task(scheduler.run_by_async())", content)
        self.assertIn("class ApplicationBootstrap", container_content)
        self.assertIn("def build_bootstrap", container_content)
        self.assertNotIn("config = Config()", content)
        self.assertIn("def create_app(config: Config)", application_content)
        self.assertNotIn("config = Config()", application_content)

    def test_config_includes_sanic_worker_settings(self):
        config_content = (SRC / "core/config/__init__.py").read_text(encoding="utf-8")
        base_yaml = (SRC / "core/config/base.yaml").read_text(encoding="utf-8")
        dev_yaml = (SRC / "core/config/dev.yaml").read_text(encoding="utf-8")
        sample_yaml = (SRC / "core/config/sample.yaml").read_text(encoding="utf-8")
        schema = json.loads((SRC / "core/config/schema.json").read_text(encoding="utf-8"))

        self.assertIn("sanic_workers: int = 1", config_content)
        self.assertIn("sanic_workers: 1", base_yaml)
        self.assertIn("sanic_workers: 1", dev_yaml)
        self.assertIn("sanic_workers: 1", sample_yaml)
        self.assertIn("sanic_workers", schema["properties"])
        self.assertEqual(schema["properties"]["sanic_workers"]["minimum"], 1)

    def test_request_handling_only_enriches_context_and_logs_safely(self):
        content = (SRC / "middleware/request_handling/request_handling.py").read_text(encoding="utf-8")
        support_content = (SRC / "domains/identity_access/presentation/http/support.py").read_text(encoding="utf-8")
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
        users_controller = (SRC / "domains/identity_access/presentation/http/admin/users.py").read_text(encoding="utf-8")
        roles_controller = (SRC / "domains/identity_access/presentation/http/admin/roles.py").read_text(encoding="utf-8")
        permissions_controller = (SRC / "domains/identity_access/presentation/http/admin/permissions.py").read_text(encoding="utf-8")
        endpoints_controller = (SRC / "domains/identity_access/presentation/http/admin/endpoints.py").read_text(encoding="utf-8")
        audit_repository = (SRC / "domains/audit/infrastructure/repositories.py").read_text(encoding="utf-8")

        self.assertIn("class PageResult", content)
        self.assertIn("return PageResult(", content)
        self.assertIn("page_result = await self.user_service.list_users", users_controller)
        self.assertIn("page_result = await self.role_service.list_roles", roles_controller)
        self.assertIn("page_result = await self.permission_service.list_permissions", permissions_controller)
        self.assertIn("page_result = await self.endpoint_service.list_endpoints", endpoints_controller)
        self.assertIn("page_result = await paginate_query", audit_repository)

    def test_routes_are_explicitly_registered(self):
        content = (SRC / "app/bootstrap/routes.py").read_text(encoding="utf-8")
        self.assertIn("def build_blueprints", content)
        self.assertIn("def register_routes", content)
        self.assertIn("register_identity_access_routes", content)
        self.assertIn("register_audit_routes", content)
        self.assertIn("register_operations_routes", content)
        self.assertIn("register_health_routes", content)
        self.assertIn("ApplicationBootstrap", content)
        self.assertIn('Blueprint(name="system"', content)
        self.assertNotIn("_routes_registered", content)
        self.assertNotIn("UserBlueprint =", content)
        self.assertNotIn("AdminBlueprint =", content)
        self.assertNotIn("def load_routes", content)
        self.assertNotIn("# noqa: F401", content)

    def test_identity_access_is_assembled_through_bootstrap(self):
        bootstrap_content = (SRC / "app/bootstrap/identity_access.py").read_text(encoding="utf-8")
        container_content = (SRC / "app/bootstrap/container.py").read_text(encoding="utf-8")
        ports_content = (SRC / "domains/identity_access/application/ports.py").read_text(encoding="utf-8")
        auth_content = (SRC / "domains/identity_access/application/use_cases/auth.py").read_text(encoding="utf-8")
        users_content = (SRC / "domains/identity_access/application/use_cases/users.py").read_text(encoding="utf-8")
        bootstrap_use_case_content = (SRC / "domains/identity_access/application/use_cases/bootstrap.py").read_text(encoding="utf-8")
        authorization_content = (SRC / "domains/identity_access/application/authorization.py").read_text(encoding="utf-8")
        user_auth_handler_content = (SRC / "domains/identity_access/presentation/http/user/auth.py").read_text(encoding="utf-8")

        self.assertIn("class IdentityAccessBootstrap", bootstrap_content)
        self.assertIn("@dataclass(slots=True)", bootstrap_content)
        self.assertIn("config: Config", bootstrap_content)
        self.assertIn("user_repository: UserRepository", bootstrap_content)
        self.assertIn("auth_service: AuthService", bootstrap_content)
        self.assertIn("jwt_auth: JwtAuth", bootstrap_content)
        self.assertIn("IdentityAccessBootstrap(", container_content)
        self.assertIn("AuthorizationService(", container_content)
        self.assertIn("AuthService(", container_content)
        self.assertIn("UserAdminService(", container_content)
        self.assertIn("JwtAuth(", container_content)
        self.assertIn("class AuditLogWriter", ports_content)
        self.assertNotIn("cached_property", bootstrap_content)
        self.assertNotIn("infra.security.passwords", auth_content)
        self.assertNotIn("infra.security.passwords", users_content)
        self.assertNotIn("infra.security.passwords", bootstrap_use_case_content)
        self.assertNotIn("from infra.redis import RedisClient", authorization_content)
        self.assertNotIn("AuditLogService()", auth_content)
        self.assertNotIn("AuditLogService()", users_content)
        self.assertNotIn("AuditLogService()", authorization_content)
        self.assertNotIn("audit_logs", auth_content)
        self.assertNotIn("audit_logs", users_content)
        self.assertNotIn("audit_logs", authorization_content)
        self.assertNotIn("from app.bootstrap.identity_access import", user_auth_handler_content)

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
        application_content = (SRC / "domains/operations/application/jobs.py").read_text(encoding="utf-8")
        ports_content = (SRC / "domains/operations/application/ports.py").read_text(encoding="utf-8")
        domain_content = (SRC / "domains/operations/domain/jobs.py").read_text(encoding="utf-8")
        handler_content = (SRC / "domains/operations/presentation/http/admin/jobs.py").read_text(encoding="utf-8")
        bootstrap_content = (SRC / "app/bootstrap/operations.py").read_text(encoding="utf-8")
        container_content = (SRC / "app/bootstrap/container.py").read_text(encoding="utf-8")
        gateway_content = (SRC / "domains/operations/infrastructure/scheduler_gateway.py").read_text(encoding="utf-8")

        self.assertIn("SchedulerJob", application_content)
        self.assertIn("SchedulerJobUpdate", application_content)
        self.assertIn("class SchedulerJobsPort", ports_content)
        self.assertIn("SchedulerJobUpdate", handler_content)
        self.assertIn("class SchedulerJob", domain_content)
        self.assertIn("class SchedulerJobUpdate", domain_content)
        self.assertIn("class OperationsBootstrap", bootstrap_content)
        self.assertIn("@dataclass(slots=True)", bootstrap_content)
        self.assertIn("scheduler: Scheduler", bootstrap_content)
        self.assertIn("scheduler_gateway: SchedulerGateway", bootstrap_content)
        self.assertIn("scheduler_job_service: SchedulerJobService", bootstrap_content)
        self.assertIn("OperationsBootstrap(", container_content)
        self.assertIn("SchedulerJobService(jobs=scheduler_gateway)", container_content)
        self.assertNotIn("from ..infrastructure", application_content)
        self.assertNotIn("def set_job", gateway_content)
        self.assertNotIn("from app.bootstrap.operations import", handler_content)

    def test_audit_context_uses_domain_log_contracts(self):
        bootstrap_content = (SRC / "app/bootstrap/audit.py").read_text(encoding="utf-8")
        container_content = (SRC / "app/bootstrap/container.py").read_text(encoding="utf-8")
        ports_content = (SRC / "domains/audit/application/ports.py").read_text(encoding="utf-8")
        domain_content = (SRC / "domains/audit/domain/logs.py").read_text(encoding="utf-8")
        application_content = (SRC / "domains/audit/application/logs.py").read_text(encoding="utf-8")
        repository_content = (SRC / "domains/audit/infrastructure/repositories.py").read_text(encoding="utf-8")
        handler_content = (SRC / "domains/audit/presentation/http/admin/logs.py").read_text(encoding="utf-8")

        self.assertIn("class AuditBootstrap", bootstrap_content)
        self.assertIn("@dataclass(slots=True)", bootstrap_content)
        self.assertIn("audit_log_repository: AuditLogRepository", bootstrap_content)
        self.assertIn("audit_log_service: AuditLogService", bootstrap_content)
        self.assertIn("AuditBootstrap(", container_content)
        self.assertIn("AuditLogService(logs=audit_log_repository)", container_content)
        self.assertIn("class AuditLogStore", ports_content)
        self.assertIn("class AuditLogRecord", domain_content)
        self.assertIn("class AuditLogQuery", domain_content)
        self.assertIn("class AuditLogPage", domain_content)
        self.assertIn("AuditLogRecord", application_content)
        self.assertIn("AuditLogQuery", application_content)
        self.assertNotIn("from ..infrastructure", application_content)
        self.assertIn("AuditLogPage", repository_content)
        self.assertIn("AuditLogQuery", handler_content)
        self.assertNotIn("AuditLogService()", handler_content)
        self.assertNotIn("from app.bootstrap.audit import", handler_content)

    def test_routing_requires_explicit_jwt_auth_when_authorizing(self):
        content = (SRC / "app/bootstrap/routing.py").read_text(encoding="utf-8")
        self.assertIn("def build_route_name", content)
        self.assertIn("name=name or build_route_name(handler)", content)
        self.assertIn("if jwt_auth is None", content)
        self.assertIn('raise ValueError("jwt_auth is required when authorize=True")', content)
        self.assertNotIn("get_jwt_auth", content)

    def test_http_layers_use_controllers_instead_of_route_local_closures(self):
        expected = {
            "domains/identity_access/presentation/http/user/auth.py": "class UserAuthController",
            "domains/identity_access/presentation/http/user/dashboard.py": "class DashboardController",
            "domains/identity_access/presentation/http/admin/users.py": "class UserAdminController",
            "domains/identity_access/presentation/http/admin/roles.py": "class RoleAdminController",
            "domains/identity_access/presentation/http/admin/permissions.py": "class PermissionAdminController",
            "domains/identity_access/presentation/http/admin/endpoints.py": "class EndpointAdminController",
            "domains/audit/presentation/http/admin/logs.py": "class AuditLogController",
            "domains/operations/presentation/http/admin/jobs.py": "class SchedulerJobsController",
        }
        for rel, controller_name in expected.items():
            with self.subTest(path=rel):
                content = (SRC / rel).read_text(encoding="utf-8")
                self.assertIn(controller_name, content)
                self.assertNotIn("async def register_routes", content)

    def test_prefixed_http_and_schema_files_are_removed(self):
        removed_files = [
            "domains/identity_access/presentation/http/user_auth.py",
            "domains/identity_access/presentation/http/dashboard.py",
            "domains/identity_access/presentation/http/admin_users.py",
            "domains/identity_access/presentation/http/admin_roles.py",
            "domains/identity_access/presentation/http/admin_permissions.py",
            "domains/identity_access/presentation/http/admin_endpoints.py",
            "domains/identity_access/presentation/schemas/user_auth.py",
            "domains/identity_access/presentation/schemas/dashboard.py",
            "domains/identity_access/presentation/schemas/admin_users.py",
            "domains/identity_access/presentation/schemas/admin_roles.py",
            "domains/identity_access/presentation/schemas/admin_permissions.py",
            "domains/identity_access/presentation/schemas/admin_endpoints.py",
            "domains/audit/presentation/http/admin_logs.py",
            "domains/audit/presentation/schemas/admin_logs.py",
            "domains/operations/presentation/http/admin_jobs.py",
            "domains/operations/presentation/schemas/admin_jobs.py",
        ]
        for rel in removed_files:
            with self.subTest(path=rel):
                self.assertFalse((SRC / rel).exists(), rel)

    def test_presentation_packages_own_route_group_registration(self):
        identity_http_content = (SRC / "domains/identity_access/presentation/http/__init__.py").read_text(encoding="utf-8")
        identity_admin_content = (SRC / "domains/identity_access/presentation/http/admin/__init__.py").read_text(
            encoding="utf-8"
        )
        identity_user_content = (SRC / "domains/identity_access/presentation/http/user/__init__.py").read_text(
            encoding="utf-8"
        )
        audit_admin_content = (SRC / "domains/audit/presentation/http/admin/__init__.py").read_text(encoding="utf-8")
        operations_admin_content = (SRC / "domains/operations/presentation/http/admin/__init__.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("register_admin_routes", identity_http_content)
        self.assertIn("register_user_routes", identity_http_content)
        self.assertNotIn("register_admin_user_routes", identity_http_content)
        self.assertNotIn("register_user_auth_routes", identity_http_content)
        self.assertIn("def register_routes", identity_admin_content)
        self.assertIn("def register_routes", identity_user_content)
        self.assertIn("def register_routes", audit_admin_content)
        self.assertIn("def register_routes", operations_admin_content)

    def test_schema_classes_use_resource_focused_names(self):
        expected = {
            "domains/identity_access/presentation/schemas/user/auth.py": [
                "class LoginBody",
                "class RegisterBody",
                "class LoginResponse",
                "class RegisterResponse",
                "class AccountAlreadyExistsResponse",
            ],
            "domains/identity_access/presentation/schemas/user/dashboard.py": [
                "class DashboardUser",
                "class DashboardRole",
                "class DashboardPermission",
                "class DashboardEndpoint",
                "class DashboardPayload",
                "class DashboardResponse",
            ],
            "domains/identity_access/presentation/schemas/admin/users.py": [
                "class UserSummary",
                "class UserListQuery",
                "class CreateUserBody",
                "class UpdateUserBody",
                "class AssignUserRoleBody",
                "class RemoveUserRoleBody",
                "class UserListResponse",
            ],
            "domains/identity_access/presentation/schemas/admin/roles.py": [
                "class RoleSummary",
                "class RoleListQuery",
                "class CreateRoleBody",
                "class UpdateRoleBody",
                "class DeleteRoleBody",
                "class AssignRolePermissionBody",
                "class RemoveRolePermissionBody",
                "class RoleListResponse",
            ],
        }
        forbidden = [
            "class UserPostLoginBody",
            "class UserPostRegisterBody",
            "class UserPostLoginSuccessfullyResponse",
            "class UserGetDashboardUserModel",
            "class AdminGetUsersQuery",
            "class AdminPostUsersBody",
            "class AdminGetRolesQuery",
            "class AdminPostRolesBody",
            "class AdminDeleteRolesPermissionsBody",
        ]
        for rel, snippets in expected.items():
            with self.subTest(path=rel):
                content = (SRC / rel).read_text(encoding="utf-8")
                for snippet in snippets:
                    self.assertIn(snippet, content)
                for snippet in forbidden:
                    self.assertNotIn(snippet, content)

    def test_http_controller_methods_use_action_names_not_route_names(self):
        http_files = [
            "domains/identity_access/presentation/http/user/auth.py",
            "domains/identity_access/presentation/http/user/dashboard.py",
            "domains/identity_access/presentation/http/admin/users.py",
            "domains/identity_access/presentation/http/admin/roles.py",
            "domains/identity_access/presentation/http/admin/permissions.py",
            "domains/identity_access/presentation/http/admin/endpoints.py",
            "domains/audit/presentation/http/admin/logs.py",
            "domains/operations/presentation/http/admin/jobs.py",
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
        support_content = (SRC / "domains/identity_access/presentation/http/support.py").read_text(encoding="utf-8")
        users_controller_content = (SRC / "domains/identity_access/presentation/http/admin/users.py").read_text(
            encoding="utf-8"
        )
        auth_controller_content = (SRC / "domains/identity_access/presentation/http/user/auth.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("def schema_response", core_http_content)
        self.assertIn("def schema_from", support_content)
        self.assertIn("def schema_list_from", support_content)
        self.assertIn("def response_from", support_content)
        self.assertIn("def invalid_arguments_response", support_content)
        self.assertNotIn("def args_invalid_response", support_content)
        self.assertNotIn("from core.http import http_response", users_controller_content)
        self.assertNotIn("from core.http import http_response", auth_controller_content)
        self.assertNotIn("args_invalid_response", users_controller_content)

    def test_identity_access_admin_use_cases_use_explicit_contracts(self):
        selectors_content = (SRC / "domains/identity_access/domain/selectors.py").read_text(encoding="utf-8")
        contracts_content = (SRC / "domains/identity_access/application/contracts.py").read_text(encoding="utf-8")
        users_service_content = (SRC / "domains/identity_access/application/use_cases/users.py").read_text(
            encoding="utf-8"
        )
        roles_service_content = (SRC / "domains/identity_access/application/use_cases/roles.py").read_text(
            encoding="utf-8"
        )
        permissions_service_content = (SRC / "domains/identity_access/application/use_cases/permissions.py").read_text(
            encoding="utf-8"
        )
        endpoints_service_content = (SRC / "domains/identity_access/application/use_cases/endpoints.py").read_text(
            encoding="utf-8"
        )
        users_repo_content = (SRC / "domains/identity_access/infrastructure/repos/users.py").read_text(encoding="utf-8")
        roles_repo_content = (SRC / "domains/identity_access/infrastructure/repos/roles.py").read_text(encoding="utf-8")
        permissions_repo_content = (SRC / "domains/identity_access/infrastructure/repos/permissions.py").read_text(
            encoding="utf-8"
        )
        endpoints_repo_content = (SRC / "domains/identity_access/infrastructure/repos/endpoints.py").read_text(
            encoding="utf-8"
        )
        users_controller_content = (SRC / "domains/identity_access/presentation/http/admin/users.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("class UserListQuery", selectors_content)
        self.assertIn("class RoleReference", selectors_content)
        self.assertIn("class EndpointReference", selectors_content)
        self.assertIn("class UserRoleBinding", contracts_content)
        self.assertIn("class RolePermissionBinding", contracts_content)
        self.assertIn("class EndpointPermissionBinding", contracts_content)
        self.assertNotIn("list_users(self, filters: dict", users_service_content)
        self.assertNotIn("update_user(self, user_id: int, updates: dict", users_service_content)
        self.assertNotIn("list_roles(self, filters: dict", roles_service_content)
        self.assertNotIn("delete_role(self, filters: dict", roles_service_content)
        self.assertNotIn("list_permissions(self, filters: dict", permissions_service_content)
        self.assertNotIn("delete_permission(self, filters: dict", permissions_service_content)
        self.assertNotIn("list_endpoints(self, filters: dict", endpoints_service_content)
        self.assertNotIn("async def list(self, filters: dict", users_repo_content)
        self.assertNotIn("async def list(self, filters: dict", roles_repo_content)
        self.assertNotIn("async def delete(self, filters: dict", roles_repo_content)
        self.assertNotIn("async def list(self, filters: dict", permissions_repo_content)
        self.assertNotIn("async def delete(self, filters: dict", permissions_repo_content)
        self.assertNotIn("async def list(self, filters: dict", endpoints_repo_content)
        self.assertIn("domain import RoleReference", users_controller_content)

    def test_endpoint_sync_job_uses_application_service_instead_of_orm(self):
        content = (SRC / "infra/scheduler/jobs/update_endpoint/task.py").read_text(encoding="utf-8")
        self.assertIn("EndpointRegistrySyncService", content)
        self.assertIn("SanicRouteCatalog", content)
        self.assertNotIn("domains.identity_access.infrastructure.models", content)
        self.assertNotIn("import sanic", content)
        self.assertNotIn("Endpoint.create", content)

    def test_config_loader_uses_yaml(self):
        content = (SRC / "core/config/__init__.py").read_text(encoding="utf-8")
        schema_content = (SRC / "core/config/schema.json").read_text(encoding="utf-8")
        self.assertIn("yaml.safe_load", content)
        self.assertIn("def load_config()", content)
        self.assertIn('cls._config_dir / "base.yaml"', content)
        self.assertIn('cls._config_dir / "sample.yaml"', content)
        self.assertIn("@dataclass", content)
        self.assertIn("class ConfigModel", content)
        self.assertIn("def apply_runtime_paths", content)
        self.assertNotRegex(content, re.compile(r"^\s*_instance\s*=", re.MULTILINE))
        self.assertNotRegex(content, re.compile(r"^\s*def __new__\(", re.MULTILINE))
        self.assertNotIn("SimpleNamespace", content)
        self.assertIn('"additionalProperties": false', schema_content)
        self.assertIn('"app"', schema_content)
        self.assertIn('"jwt_secret_key"', schema_content)
        self.assertIn('"migrations_path"', schema_content)
        self.assertNotIn('"APP"', schema_content)
        self.assertNotIn('"JwtSecretKey"', schema_content)
        self.assertNotIn('"auto_generate_schema"', schema_content)

    def test_yaml_config_files_reference_schema(self):
        for rel in ["core/config/base.yaml", "core/config/sample.yaml", "core/config/dev.yaml"]:
            with self.subTest(path=rel):
                first_line = (SRC / rel).read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first_line, "# yaml-language-server: $schema=./schema.json")

    def test_database_uses_explicit_orm_metadata(self):
        database_content = (SRC / "app/bootstrap/database.py").read_text(encoding="utf-8")
        models_content = (SRC / "domains/identity_access/infrastructure/models.py").read_text(encoding="utf-8")
        audit_models_content = (SRC / "domains/audit/infrastructure/models.py").read_text(encoding="utf-8")

        self.assertIn("ORM_MODEL_MODULES", database_content)
        self.assertIn("cfg.app", database_content)
        self.assertIn("class TortoiseClient", database_content)
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
        content = PYPROJECT.read_text(encoding="utf-8")
        self.assertIn("[tool.aerich]", content)
        self.assertIn('tortoise_orm = "app.bootstrap.migrations.TORTOISE_ORM"', content)
        self.assertIn('location = "./migrations"', content)
        self.assertIn('src = "./src"', content)

    def test_http_response_uses_result_key(self):
        try:
            import yaml  # noqa: F401
            import sanic  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("YAML or Sanic dependencies are not installed in the current interpreter")

        sys.path.insert(0, str(SRC))
        try:
            from core.http import http_response

            payload = json.loads(http_response(0, "ok", result={"id": 1}).body)
            self.assertEqual(payload["code"], 0)
            self.assertEqual(payload["msg"], "ok")
            self.assertEqual(payload["result"], {"id": 1})
            self.assertNotIn("results", payload)
            with self.assertRaises(TypeError):
                http_response(0, "ok", results=[1, 2])
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
        ports_content = (SRC / "domains/identity_access/application/ports.py").read_text(encoding="utf-8")
        security_content = (SRC / "domains/identity_access/infrastructure/security.py").read_text(encoding="utf-8")
        password_content = (SRC / "infra/security/passwords.py").read_text(encoding="utf-8")
        auth_content = (SRC / "domains/identity_access/application/use_cases/auth.py").read_text(encoding="utf-8")

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
        identity_auth_schema_content = (SRC / "domains/identity_access/presentation/schemas/user/auth.py").read_text(encoding="utf-8")
        audit_logs_content = (SRC / "domains/audit/application/logs.py").read_text(encoding="utf-8")
        operations_jobs_content = (SRC / "domains/operations/application/jobs.py").read_text(encoding="utf-8")
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
            from app.bootstrap.migrations import TORTOISE_ORM
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
        self.assertIn("from app.bootstrap.container import build_bootstrap", content)
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
        self.assertNotIn("domains.identity_access.infrastructure.models", content)
        self.assertNotIn("from infra.security import generate_openid", content)
        self.assertNotIn('@click.option("--pre"', content)
        self.assertNotIn('command.extend(["--pre", pre])', content)
        self.assertIn('cli.command("seed_identity_access")', content)
        self.assertIn('cli.command("migration_init_migrations")', content)
        self.assertIn('cli.command("migration_doctor")', content)

    def test_legacy_schema_dump_is_removed(self):
        self.assertFalse((SRC / "scripts/ops/demo.sql").exists())
        self.assertFalse((ROOT / "docs" / "legacy" / "sql" / "demo.sql").exists())

    def test_blueprints_can_be_imported_when_web_dependencies_are_installed(self):
        try:
            import yaml  # noqa: F401
            import sanic  # noqa: F401
            import sanic_ext  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("YAML or Sanic dependencies are not installed in the current interpreter")

        sys.path.insert(0, str(SRC))
        try:
            from app.bootstrap.container import build_bootstrap
            from app.bootstrap.routes import get_blueprints
            from app.bootstrap.runtime import build_runtime
            from core.config import load_config
            from sanic import Sanic

            config = load_config()
            blueprints = get_blueprints(build_bootstrap())
            self.assertEqual([blueprint.name for blueprint in blueprints], ["user", "admin", "system"])

            Sanic._app_registry.pop(config.app, None)
            server = build_runtime(config).build_http_server()
            self.assertEqual(server.name, config.app)
            Sanic._app_registry.pop(config.app, None)
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
