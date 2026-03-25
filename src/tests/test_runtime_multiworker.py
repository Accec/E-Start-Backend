import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class RuntimeMultiWorkerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_single_worker_http_server_does_not_touch_scheduler(self):
        try:
            from app.bootstrap.runtime import build_runtime
            from core.config import load_config
        except ModuleNotFoundError as exc:
            self.skipTest(f"Sanic dependencies are unavailable: {exc}")

        class FakeAsyncioServer:
            def __init__(self):
                self.started = False
                self.closed = False

            async def startup(self):
                self.started = True

            async def serve_forever(self):
                return None

            def close(self):
                self.closed = True

            async def wait_closed(self):
                return None

        class FakeHttpServer:
            def __init__(self):
                self.asyncio_server = FakeAsyncioServer()

            async def create_server(self, **kwargs):
                return self.asyncio_server

        config = replace(load_config(), sanic_workers=1)
        runtime = build_runtime(config)
        fake_server = FakeHttpServer()

        def fail_build_scheduler():
            raise AssertionError("HTTP mode must not build or start the scheduler")

        with (
            patch.object(type(runtime), "setup_logging", lambda self: None),
            patch.object(type(runtime), "build_http_server", lambda self: fake_server),
            patch.object(type(runtime), "build_scheduler", lambda self: fail_build_scheduler()),
        ):
            await runtime.start_single_worker_http_server()

        self.assertTrue(fake_server.asyncio_server.started)
        self.assertTrue(fake_server.asyncio_server.closed)

    def test_http_server_can_be_prepared_with_multiple_workers(self):
        try:
            from sanic import Sanic
            from app.bootstrap.runtime import build_http_server_from_config
            from core.config import load_config
        except ModuleNotFoundError as exc:
            self.skipTest(f"Sanic dependencies are unavailable: {exc}")

        config = replace(load_config(), sanic_workers=2)
        Sanic._app_registry.pop(config.app, None)

        server = build_http_server_from_config(config)
        try:
            server.prepare(
                host=config.sanic_host,
                port=config.sanic_port,
                debug=config.debug,
                access_log=False,
                workers=config.sanic_workers,
            )
            self.assertEqual(server.state.workers, 2)
            self.assertTrue(server.state.server_info)
        finally:
            server.state.server_info.clear()
            Sanic._app_registry.pop(config.app, None)


if __name__ == "__main__":
    unittest.main()
