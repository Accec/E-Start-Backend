import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sanic import Sanic

from app import create_app, create_http_app
from core.config import Config


class ApplicationTestCase(unittest.TestCase):
    def setUp(self):
        self.config = Config(app="TestApplication", jwt_secret_key="test-secret-key-" * 3)
        self.addCleanup(Sanic._app_registry.pop, self.config.app, None)
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)

    def test_application_passes_explicit_services_and_the_same_config(self):
        redis_client, scheduler = Mock(), Mock()
        with (
            patch("app.register_database") as database,
            patch("app.setup_application_loggers"),
            patch("app.register_identity_access_routes") as identity,
            patch("app.register_audit_routes") as audit,
            patch("app.register_operations_routes") as operations,
            patch("app.register_health_routes") as health,
        ):
            server = create_app(self.config, redis_client, scheduler)

        self.assertIsInstance(server, Sanic)
        database.assert_called_once_with(server, self.config)
        services = identity.call_args.kwargs
        self.assertEqual(set(services), {
            "auth_service", "dashboard_service", "user_service", "role_service",
            "permission_service", "endpoint_service", "jwt_auth",
        })
        self.assertIs(services["auth_service"].users, services["user_service"].users)
        self.assertIs(services["user_service"].roles, services["role_service"].roles)
        self.assertIs(services["user_service"].audit_logger, audit.call_args.kwargs["audit_service"])
        self.assertIs(services["jwt_auth"], audit.call_args.kwargs["jwt_auth"])
        self.assertIs(services["jwt_auth"], operations.call_args.kwargs["jwt_auth"])
        self.assertIs(operations.call_args.kwargs["job_service"].jobs.scheduler, scheduler)
        self.assertEqual(health.call_args.kwargs, {
            "app_name": self.config.app, "redis_client": redis_client,
        })
        for dependency in (*services.values(), redis_client, scheduler):
            self.assertTrue(all(value is not dependency for value in vars(server.ctx).values()))

    def test_http_factory_creates_independent_resources_without_starting_them(self):
        clients = [Mock(), Mock()]
        schedulers = [Mock(), Mock()]
        with (
            patch("app.RedisClient", side_effect=clients) as redis_type,
            patch("app.Scheduler", side_effect=schedulers) as scheduler_type,
            patch("app.create_app") as application,
        ):
            first = create_http_app(self.config)
            second = create_http_app(self.config)

        self.assertIs(first, application.return_value)
        self.assertIs(second, application.return_value)
        self.assertEqual(redis_type.call_count, 2)
        for index in range(2):
            self.assertEqual(redis_type.call_args_list[index].args, (self.config.redis_url,))
            self.assertEqual(scheduler_type.call_args_list[index].args, (clients[index],))
            self.assertEqual(application.call_args_list[index].args,
                             (self.config, clients[index], schedulers[index]))
            schedulers[index].start.assert_not_called()

    def test_real_application_can_be_prepared_for_two_workers(self):
        self.config.sanic_workers = 2
        with patch("app.setup_application_loggers"):
            server = create_http_app(self.config)
        try:
            server.prepare(
                host=self.config.sanic_host, port=self.config.sanic_port,
                debug=self.config.debug, access_log=False, workers=2,
            )
            self.assertEqual(server.state.workers, 2)
            self.assertTrue(server.state.server_info)
            routes = {(route.path, method) for route in server.router.routes_all.values()
                      for method in route.methods}
            self.assertIn(("api/v1/system/health", "GET"), routes)
            self.assertIn(("api/v1/system/ready", "GET"), routes)
        finally:
            server.state.server_info.clear()


if __name__ == "__main__":
    unittest.main()
