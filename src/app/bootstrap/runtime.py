import asyncio
from dataclasses import dataclass, field
import logging

from app.bootstrap.application import create_app
from app.bootstrap.container import ApplicationBootstrap, build_bootstrap
from app.bootstrap.database import close_database, init_database
from app.bootstrap.logging import setup_application_loggers
from app.bootstrap.routes import get_blueprints
from core.config import Config, load_config
from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER
from middleware.request_handling.request_handling import request_handling

@dataclass(slots=True)
class ApplicationRuntime:
    config: Config
    logger: logging.Logger = field(init=False, repr=False)
    bootstrap: ApplicationBootstrap = field(init=False, repr=False)

    def __post_init__(self):
        self.logger = logging.getLogger(SERVER_LOGGER)
        self.bootstrap = build_bootstrap(self.config)

    def build_http_server(self):
        server = create_app(self.config)
        server.middleware(request_handling)

        for blueprint in get_blueprints(self.bootstrap):
            self.logger.info("[Blueprint] - [%s] is loaded", blueprint.name)
            server.blueprint(blueprint)

        return server

    def build_scheduler(self):
        return self.bootstrap.operations.scheduler

    def bind_http_server_lifecycle(self, server, scheduler):
        @server.after_server_start
        async def start_background_services(app, loop):
            self.logger.info("Start the service")
            app.add_task(scheduler.run_by_async())

        @server.before_server_stop
        async def stop_background_services(app, loop):
            await asyncio.sleep(0.1)
            await scheduler.shutdown()
            await asyncio.get_event_loop().shutdown_asyncgens()
            self.logger.info("Stop the service")

    async def init_application(self):
        setup_application_loggers()

        logging.getLogger(API_LOGGER)
        logging.getLogger(TASK_LOGGER)
        logging.getLogger(JOB_LOGGER)
        logging.getLogger(SCHEDULER_LOGGER)
        logging.getLogger(SERVER_LOGGER)

        server = self.build_http_server()
        scheduler = self.build_scheduler()
        return server, scheduler

    async def start_http_server(self):
        server, scheduler = await self.init_application()
        self.bind_http_server_lifecycle(server, scheduler)

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

    async def start_scheduler(self):
        server, scheduler = await self.init_application()
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


async def start_http_server(config: Config | None = None):
    await build_runtime(config).start_http_server()


async def start_scheduler(config: Config | None = None):
    await build_runtime(config).start_scheduler()


__all__ = ["ApplicationRuntime", "build_runtime", "start_http_server", "start_scheduler"]
