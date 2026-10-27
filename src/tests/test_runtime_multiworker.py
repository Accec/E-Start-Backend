import asyncio
import pickle
import sys
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config import Config
from main import start_http_server, start_scheduler, start_single_worker_http_server


class RuntimeMultiWorkerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_single_worker_serves_and_closes_without_starting_scheduler(self):
        config = Config(sanic_workers=1)
        asyncio_server = Mock(
            startup=AsyncMock(), serve_forever=AsyncMock(), wait_closed=AsyncMock(),
            before_start=AsyncMock(), after_start=AsyncMock(),
            before_stop=AsyncMock(), after_stop=AsyncMock(),
        )
        server = Mock(create_server=AsyncMock(return_value=asyncio_server))
        with (
            patch("app.create_http_app", return_value=server) as factory,
            patch("infra.scheduler.Scheduler.start", new_callable=AsyncMock) as scheduler_start,
        ):
            await start_single_worker_http_server(config)

        factory.assert_called_once_with(config)
        server.create_server.assert_awaited_once_with(
            host=config.sanic_host, port=config.sanic_port, debug=config.debug,
            access_log=False, return_asyncio_server=True,
        )
        asyncio_server.startup.assert_awaited_once_with()
        asyncio_server.serve_forever.assert_awaited_once_with()
        asyncio_server.close.assert_called_once_with()
        asyncio_server.wait_closed.assert_awaited_once_with()
        self.assertEqual([call[0] for call in asyncio_server.method_calls], [
            "startup", "before_start", "after_start", "serve_forever",
            "before_stop", "close", "wait_closed", "after_stop",
        ])
        scheduler_start.assert_not_awaited()

    async def test_single_worker_closes_server_when_startup_fails(self):
        asyncio_server = Mock(
            startup=AsyncMock(side_effect=RuntimeError("startup failed")),
            serve_forever=AsyncMock(), wait_closed=AsyncMock(),
        )
        server = Mock(create_server=AsyncMock(return_value=asyncio_server))
        with patch("app.create_http_app", return_value=server):
            with self.assertRaisesRegex(RuntimeError, "startup failed"):
                await start_single_worker_http_server(Config())
        asyncio_server.serve_forever.assert_not_awaited()
        asyncio_server.close.assert_called_once_with()
        asyncio_server.wait_closed.assert_awaited_once_with()

    async def test_single_worker_closes_resources_when_a_lifecycle_listener_fails(self):
        for listener in ("before_start", "after_start", "before_stop"):
            with self.subTest(listener=listener):
                asyncio_server = Mock(
                    startup=AsyncMock(), serve_forever=AsyncMock(), wait_closed=AsyncMock(),
                    before_start=AsyncMock(), after_start=AsyncMock(),
                    before_stop=AsyncMock(), after_stop=AsyncMock(),
                )
                getattr(asyncio_server, listener).side_effect = RuntimeError("listener failed")
                server = Mock(create_server=AsyncMock(return_value=asyncio_server))
                with patch("app.create_http_app", return_value=server):
                    with self.assertRaisesRegex(RuntimeError, "listener failed"):
                        await start_single_worker_http_server(Config())
                asyncio_server.close.assert_called_once_with()
                asyncio_server.wait_closed.assert_awaited_once_with()
                asyncio_server.after_stop.assert_awaited_once_with()

    def test_multiworker_passes_a_factory_not_live_resources_to_app_loader(self):
        config = Config(sanic_workers=2)
        primary = Mock()
        with (
            patch("app.create_http_app", return_value=primary) as factory,
            patch("sanic.worker.loader.AppLoader") as loader,
            patch("sanic.Sanic.serve") as serve,
            patch("infra.scheduler.Scheduler.start", new_callable=AsyncMock) as scheduler_start,
        ):
            start_http_server(config)
        factory.assert_called_once_with(config)
        primary.prepare.assert_called_once_with(
            host=config.sanic_host, port=config.sanic_port, debug=config.debug,
            access_log=False, workers=2,
        )
        worker_factory = loader.call_args.kwargs["factory"]
        self.assertIs(worker_factory.func, factory)
        self.assertEqual(worker_factory.args, (config,))
        self.assertEqual(worker_factory.keywords, {})
        serve.assert_called_once_with(primary=primary, app_loader=loader.return_value)
        scheduler_start.assert_not_awaited()

    def test_worker_factory_can_be_pickled(self):
        from app import create_http_app

        config = Config(sanic_workers=2)
        restored = pickle.loads(pickle.dumps(partial(create_http_app, config)))
        self.assertIs(restored.func, create_http_app)
        self.assertEqual(restored.args, (config,))

    async def test_scheduler_owns_resources_and_cleans_up_on_interrupt_or_failure(self):
        for failure in ("wait", "database", "scheduler"):
            with self.subTest(failure=failure):
                config = Config()
                scheduler = Mock(start=AsyncMock(), shutdown=AsyncMock())
                init_database = AsyncMock()
                if failure == "database":
                    init_database.side_effect = RuntimeError("database failed")
                elif failure == "scheduler":
                    scheduler.start.side_effect = RuntimeError("scheduler failed")

                with (
                    patch("infra.redis.RedisClient") as redis,
                    patch("infra.scheduler.Scheduler", return_value=scheduler) as scheduler_type,
                    patch("app.create_app") as create_app,
                    patch("infra.database.init_database", init_database),
                    patch("infra.database.close_database", new_callable=AsyncMock) as close_database,
                    patch("main.asyncio.sleep", new_callable=AsyncMock,
                          side_effect=asyncio.CancelledError) as sleep,
                ):
                    expected = asyncio.CancelledError if failure == "wait" else RuntimeError
                    with self.assertRaises(expected):
                        await start_scheduler(config)

                redis.assert_called_once_with(config.redis_url)
                scheduler_type.assert_called_once_with(redis.return_value)
                create_app.assert_called_once_with(config, redis.return_value, scheduler)
                create_app.return_value.create_server.assert_not_called()
                create_app.return_value.prepare.assert_not_called()
                init_database.assert_awaited_once_with(config)
                self.assertEqual(scheduler.start.await_count, 0 if failure == "database" else 1)
                self.assertEqual(sleep.await_count, 1 if failure == "wait" else 0)
                scheduler.shutdown.assert_awaited_once_with()
                close_database.assert_awaited_once_with()

    async def test_database_closes_even_if_scheduler_shutdown_fails(self):
        scheduler = Mock(
            start=AsyncMock(), shutdown=AsyncMock(side_effect=RuntimeError("shutdown failed")),
        )
        with (
            patch("infra.redis.RedisClient"),
            patch("infra.scheduler.Scheduler", return_value=scheduler),
            patch("app.create_app"),
            patch("infra.database.init_database", new_callable=AsyncMock),
            patch("infra.database.close_database", new_callable=AsyncMock) as close_database,
            patch("main.asyncio.sleep", new_callable=AsyncMock, side_effect=asyncio.CancelledError),
        ):
            with self.assertRaisesRegex(RuntimeError, "shutdown failed"):
                await start_scheduler(Config())
        close_database.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
