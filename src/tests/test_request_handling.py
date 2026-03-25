import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class FakeMultiMapping:
    def __init__(self, data):
        self.data = {key: value if isinstance(value, list) else [value] for key, value in data.items()}

    def keys(self):
        return self.data.keys()

    def get(self, key):
        values = self.data[key]
        return values[0] if values else None

    def getlist(self, key):
        return list(self.data[key])


class FakeLogger:
    def __init__(self):
        self.infos = []
        self.warnings = []

    def info(self, message, *args):
        self.infos.append((message, args))

    def warning(self, message, *args):
        self.warnings.append((message, args))


class RequestHandlingTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_request_handling_sets_context_and_logs_query_payload(self):
        try:
            import middleware.request_handling.request_handling as request_module
        except ModuleNotFoundError as exc:
            self.skipTest(f"Request handling dependencies are unavailable: {exc}")

        request = SimpleNamespace(
            id="req-1",
            remote_addr="127.0.0.1",
            ip="127.0.0.1",
            headers={"user-agent": "pytest"},
            uri_template="/api/v1/user/dashboard",
            path="/api/v1/user/dashboard",
            url="http://localhost/api/v1/user/dashboard?page=1&tag=a&tag=b",
            method="GET",
            content_type=None,
            args=FakeMultiMapping({"page": "1", "tag": ["a", "b"]}),
            form=FakeMultiMapping({}),
            ctx=SimpleNamespace(),
        )

        fake_logger = FakeLogger()
        original_logger = request_module.logger
        request_module.logger = fake_logger
        try:
            await request_module.request_handling(request)
        finally:
            request_module.logger = original_logger

        self.assertEqual(request.ctx.request_id, "req-1")
        self.assertEqual(request.ctx.real_ip, "127.0.0.1")
        self.assertEqual(request.ctx.ua, "pytest")
        self.assertEqual(request.ctx.request_path, "/api/v1/user/dashboard")
        self.assertEqual(len(fake_logger.infos), 1)
        self.assertEqual(fake_logger.warnings, [])

    async def test_request_handling_does_not_break_on_invalid_json(self):
        try:
            import middleware.request_handling.request_handling as request_module
        except ModuleNotFoundError as exc:
            self.skipTest(f"Request handling dependencies are unavailable: {exc}")

        class BrokenJsonRequest(SimpleNamespace):
            @property
            def json(self):
                raise ValueError("invalid json")

        request = BrokenJsonRequest(
            id="req-2",
            remote_addr=None,
            ip="10.0.0.2",
            headers={"user-agent": "pytest"},
            uri_template=None,
            path="/api/v1/user/login",
            url="http://localhost/api/v1/user/login",
            method="POST",
            content_type="application/json",
            args=FakeMultiMapping({}),
            form=FakeMultiMapping({}),
            ctx=SimpleNamespace(),
        )

        fake_logger = FakeLogger()
        original_logger = request_module.logger
        request_module.logger = fake_logger
        try:
            await request_module.request_handling(request)
        finally:
            request_module.logger = original_logger

        self.assertEqual(request.ctx.real_ip, "10.0.0.2")
        self.assertEqual(request.ctx.request_path, "/api/v1/user/login")
        self.assertEqual(fake_logger.infos, [])
        self.assertEqual(len(fake_logger.warnings), 1)


if __name__ == "__main__":
    unittest.main()
