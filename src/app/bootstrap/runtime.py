import asyncio
from dataclasses import dataclass, field
from functools import partial
import logging

from app.bootstrap.application import create_app
from app.bootstrap.container import ApplicationBootstrap, build_bootstrap
from app.bootstrap.database import close_database, init_database
from app.bootstrap.logging import setup_application_loggers
from app.bootstrap.routes import get_blueprints
from core.config import Config, load_config
from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER
from middleware.request_handling.request_handling import request_handling
from sanic import Sanic
from sanic.worker.loader import AppLoader

@dataclass(slots=True)
class ApplicationRuntime:
    config: Config
    logger: logging.Logger = field(init=False, repr=False)
    bootstrap: ApplicationBootstrap | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.logger = logging.getLogger(SERVER_LOGGER)

    def resolve_bootstrap(self):
        if self.bootstrap is None:
            self.bootstrap = build_bootstrap(self.config)
        return self.bootstrap

    def setup_logging(self):
        setup_application_loggers()

        logging.getLogger(API_LOGGER)
        logging.getLogger(TASK_LOGGER)
        logging.getLogger(JOB_LOGGER)
        logging.getLogger(SCHEDULER_LOGGER)
        logging.getLogger(SERVER_LOGGER)

    def build_http_server(self):
        server = create_app(self.config)
        server.middleware(request_handling)
        bootstrap = self.resolve_bootstrap()

        for blueprint in get_blueprints(bootstrap):
            self.logger.info("[Blueprint] - [%s] is loaded", blueprint.name)
            server.blueprint(blueprint)

        return server

    def build_scheduler(self):
        return self.resolve_bootstrap().operations.scheduler

    async def init_scheduler_application(self):
        self.setup_logging()
        server = self.build_http_server()
        scheduler = self.build_scheduler()
        return server, scheduler

    async def start_single_worker_http_server(self):
        self.setup_logging()
        server = self.build_http_server()

        asyncio_server = await server.create_server(
            host=self.config.sanic_host,
            port=self.config.sanic_port,
            debug=self.config.debug,
            access_log=False,
            return_asyncio_server=True,
        )

        try:
            await asyncio_server.startup()
            await asyncio_server.serve_forever()
        finally:
            asyncio_server.close()
            await asyncio_server.wait_closed()

    def start_multi_worker_http_server(self):
        self.setup_logging()

        server_factory = partial(build_http_server_from_config, self.config)
        primary = server_factory()
        primary.prepare(
            host=self.config.sanic_host,
            port=self.config.sanic_port,
            debug=self.config.debug,
            access_log=False,
            workers=self.config.sanic_workers,
        )
        Sanic.serve(primary=primary, app_loader=AppLoader(factory=server_factory))

    def start_http_server(self):
        if self.config.sanic_workers == 1:
            asyncio.run(self.start_single_worker_http_server())
            return

        self.start_multi_worker_http_server()

    async def start_scheduler(self):
        server, scheduler = await self.init_scheduler_application()
        await init_database(self.config)

        try:
            self.logger.info("Scheduler mode bootstrapped with Sanic app [%s]", server.name)
            await scheduler.start()
            self.logger.info("Scheduler running...")
            while True:
                await asyncio.sleep(3600)
        finally:
            await scheduler.shutdown()
            await close_database()


def build_runtime(config: Config | None = None):
    return ApplicationRuntime(config=config or load_config())


def build_http_server_from_config(config: Config | None = None):
    runtime = build_runtime(config)
    runtime.setup_logging()
    return runtime.build_http_server()


def start_http_server(config: Config | None = None):
    build_runtime(config).start_http_server()


async def start_scheduler(config: Config | None = None):
    await build_runtime(config).start_scheduler()


__all__ = ["ApplicationRuntime", "build_http_server_from_config", "build_runtime", "start_http_server", "start_scheduler"]
