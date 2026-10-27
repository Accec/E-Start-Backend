import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class HealthControllerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_registered_routes_use_explicit_readiness_dependencies(self):
        try:
            from infra.web.health import register_health_routes
        except ModuleNotFoundError as exc:
            self.skipTest(f"Health controller dependencies are unavailable: {exc}")

        blueprint = object()
        redis_client = AsyncMock()
        with (
            patch("infra.web.routing.add_route") as add_route,
            patch("infra.web.health.check_database_readiness", new_callable=AsyncMock) as database_check,
        ):
            register_health_routes(blueprint, app_name="ExplicitApp", redis_client=redis_client)
            self.assertEqual(add_route.call_count, 2)
            health_route, ready_route = add_route.call_args_list
            self.assertEqual(health_route.args, (blueprint, "/health"))
            self.assertEqual(ready_route.args, (blueprint, "/ready"))
            self.assertEqual(health_route.kwargs["methods"], ["GET"])
            self.assertEqual(ready_route.kwargs["methods"], ["GET"])

            health_response = await health_route.kwargs["handler"](None)
            self.assertEqual(json.loads(health_response.body)["results"]["app"], "ExplicitApp")
            database_check.assert_not_awaited()
            redis_client.ping.assert_not_awaited()

            ready_response = await ready_route.kwargs["handler"](None)
            payload = json.loads(ready_response.body)
            self.assertEqual(ready_response.status, 200)
            self.assertEqual(payload["results"]["app"], "ExplicitApp")
            self.assertEqual(payload["results"]["dependencies"], {"database": "ok", "redis": "ok"})
            database_check.assert_awaited_once_with()
            redis_client.ping.assert_awaited_once_with()

    async def test_health_endpoint_reports_alive(self):
        try:
            from infra.web.health import HealthController
        except ModuleNotFoundError as exc:
            self.skipTest(f"Health controller dependencies are unavailable: {exc}")

        controller = HealthController(app_name="Backend", readiness_probes=())
        response = await controller.health(None)
        payload = json.loads(response.body)

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["results"]["app"], "Backend")
        self.assertEqual(payload["results"]["status"], "alive")

    async def test_ready_endpoint_reports_dependency_failures(self):
        try:
            from infra.web.health import HealthController, ReadinessProbe
        except ModuleNotFoundError as exc:
            self.skipTest(f"Health controller dependencies are unavailable: {exc}")

        async def ok_probe():
            return None

        async def failed_probe():
            raise RuntimeError("redis unavailable")

        controller = HealthController(
            app_name="demo",
            readiness_probes=(
                ReadinessProbe(name="database", check=ok_probe),
                ReadinessProbe(name="redis", check=failed_probe),
            ),
        )
        response = await controller.ready(None)
        payload = json.loads(response.body)

        self.assertEqual(response.status, 503)
        self.assertEqual(payload["code"], -1008)
        self.assertEqual(payload["msg"], "Service unavailable")
        self.assertEqual(payload["results"]["status"], "degraded")
        self.assertEqual(payload["results"]["dependencies"]["database"], "ok")
        self.assertEqual(payload["results"]["dependencies"]["redis"], "redis unavailable")


if __name__ == "__main__":
    unittest.main()
