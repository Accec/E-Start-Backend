from __future__ import annotations

import argparse
import asyncio
from functools import partial
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import Config


async def start_single_worker_http_server(config: Config):
    from app import create_http_app

    server = create_http_app(config)
    asyncio_server = await server.create_server(
        host=config.sanic_host,
        port=config.sanic_port,
        debug=config.debug,
        access_log=False,
        return_asyncio_server=True,
    )
    started = False
    try:
        await asyncio_server.startup()
        started = True
        await asyncio_server.before_start()
        await asyncio_server.after_start()
        await asyncio_server.serve_forever()
    finally:
        try:
            if started:
                await asyncio_server.before_stop()
        finally:
            asyncio_server.close()
            try:
                await asyncio_server.wait_closed()
            finally:
                if started:
                    await asyncio_server.after_stop()


def start_http_server(config: Config | None = None):
    from app import create_http_app
    from core.config import load_config
    from sanic import Sanic
    from sanic.worker.loader import AppLoader

    config = config or load_config()
    if config.sanic_workers == 1:
        asyncio.run(start_single_worker_http_server(config))
        return

    server_factory = partial(create_http_app, config)
    primary = server_factory()
    primary.prepare(
        host=config.sanic_host,
        port=config.sanic_port,
        debug=config.debug,
        access_log=False,
        workers=config.sanic_workers,
    )
    Sanic.serve(primary=primary, app_loader=AppLoader(factory=server_factory))


async def start_scheduler(config: Config | None = None):
    from app import create_app
    from core.config import load_config
    from core.constants import SERVER_LOGGER
    from infra.database import close_database, init_database
    from infra.redis import RedisClient
    from infra.scheduler import Scheduler

    config = config or load_config()
    redis_client = RedisClient(config.redis_url)
    scheduler = Scheduler(redis_client)
    logger = logging.getLogger(SERVER_LOGGER)
    try:
        # Endpoint synchronization reads the registered routes without serving HTTP.
        server = create_app(config, redis_client, scheduler)
        await init_database(config)
        logger.info("Scheduler mode initialized with Sanic app [%s]", server.name)
        await scheduler.start()
        logger.info("Scheduler running...")
        while True:
            await asyncio.sleep(3600)
    finally:
        try:
            await scheduler.shutdown()
        finally:
            await close_database()


def cli():
    parser = argparse.ArgumentParser(description="Backend Entrypoint")
    parser.add_argument(
        "command",
        nargs="?",
        default="server",
        help="server | scheduler | <ops command>",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.command == "server":
        start_http_server()
        return

    if args.command == "scheduler":
        asyncio.run(start_scheduler())
        return

    from scripts.ops import cli as ops_cli

    ops_cli.main(args=[args.command, *args.args], prog_name="python src/main.py")


if __name__ == "__main__":
    cli()
