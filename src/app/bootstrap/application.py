import os

import sanic

from core.config import Config

from .database import register_database


def create_app(config: Config):
    server = sanic.Sanic(config.app)

    config.apply_runtime_paths(os.getcwd())

    os.environ["LOG_PATH"] = config.logs_path

    server.config.SERVER_NAME = f"{config.sanic_host}:{config.sanic_port}"
    server.config.FORWARDED_SECRET = config.forwarded_secret
    server.config.CORS_ORIGINS = ";".join(config.cors_domains)

    server.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    register_database(server)
    return server
