import logging
import os

from tortoise import Tortoise

from core.config import Config, load_config
from core.persistence import ORM_MODEL_MODULES


logger = logging.getLogger("DB")


def build_tortoise_models(include_aerich: bool = False):
    # Keep model discovery centralized so runtime startup and migration tooling
    # always operate on the same model graph.
    models = list(ORM_MODEL_MODULES)
    if include_aerich:
        models.append("aerich.models")
    return models


def build_tortoise_orm_config(config: Config | None = None, *, include_aerich: bool = False) -> dict:
    cfg = config or load_config()
    return {
        "connections": {
            "default": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": cfg.mysql_host,
                    "port": cfg.mysql_port,
                    "user": cfg.mysql_username,
                    "password": cfg.mysql_password,
                    "database": cfg.mysql_database_name,
                    "maxsize": "15",
                    "minsize": "5",
                },
            },
        },
        "apps": {
            cfg.app: {
                "models": build_tortoise_models(include_aerich=include_aerich),
                "default_connection": "default",
            }
        },
        "use_tz": True,
        "timezone": cfg.timezone,
    }


TORTOISE_ORM = build_tortoise_orm_config(include_aerich=True)


class TortoiseClient:
    def __init__(self, config: Config):
        self.config = config

    async def init_db(self):
        await Tortoise.init(config=build_tortoise_orm_config(self.config))

        # Schema generation stays opt-in because migration history, not runtime
        # side effects, must remain the source of truth in production.
        auto_schema = os.environ.get("DB_AUTO_SCHEMA", "0").lower() in ("1", "true", "yes")
        if auto_schema:
            logger.warning("[DB] DB_AUTO_SCHEMA is enabled; generate_schemas(safe=True) will run")
            await Tortoise.generate_schemas(safe=True)


async def init_database(config: Config | None = None):
    tortoise_client = TortoiseClient(config or load_config())
    await tortoise_client.init_db()


async def close_database():
    await Tortoise.close_connections()


def register_database(server):
    from tortoise.contrib.sanic import register_tortoise

    register_tortoise(
        server,
        config=build_tortoise_orm_config(),
        generate_schemas=False,
    )
