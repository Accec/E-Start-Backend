import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class HealthControllerTestCase(unittest.IsolatedAsyncioTestCase):
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
        self.assertEqual(payload["result"]["app"], "Backend")
        self.assertEqual(payload["result"]["status"], "alive")

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
        self.assertEqual(payload["result"]["status"], "degraded")
        self.assertEqual(payload["result"]["dependencies"]["database"], "ok")
        self.assertEqual(payload["result"]["dependencies"]["redis"], "redis unavailable")


if __name__ == "__main__":
    unittest.main()
