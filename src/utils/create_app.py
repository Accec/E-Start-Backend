import os
from pathlib import PurePosixPath
import sanic

from application import api

from tortoise.contrib.sanic import register_tortoise

from models import Log

import importlib
import config
import logging
from utils.constant import SERVER_LOGGER


Config = config.Config()

def create_app():
    server = sanic.Sanic(Config.APP)
    tortoise_config = {
            'connections': {
                'default': {
                    'engine': 'tortoise.backends.mysql',
                    'credentials': {
                            'host': Config.MysqlHost,
                            'port': Config.MysqlPort,
                            'user': Config.MysqlUsername,
                            'password': Config.MysqlPassword,
                            'database': Config.MysqlDatabaseName,
                        "maxsize":"15",
                        "minsize":"5"
                    }
                },
            },
            'apps': {
                Config.APP: {
                    'models': ["models"],
                    'default_connection': 'default',
                }
            },
            'use_tz': True,
        }

    cwd = os.getcwd().replace('\\','/')

    if Config.RelativePath == True:
        Config.UploadsPath = f"{cwd}/{Config.UploadsPath}"
        Config.LogsPath = f"{cwd}/{Config.LogsPath}"

    
    os.environ['LOG_PATH'] = Config.LogsPath

    server.config.SERVER_NAME = f"{Config.SanicHost}:{Config.SanicPort}"
    server.config.FORWARDED_SECRET = Config.ForwardedSecret
    server.config.CORS_ORIGINS = ";".join(Config.CorsDomains)
    
    server.ext.openapi.add_security_scheme(
        "token",
        "http",
        scheme="bearer",
        bearer_format="JWT",
    )
    register_tortoise(
            server, config = tortoise_config,
            generate_schemas=True
        )

    return server

def autodiscover_api():
    logger = logging.getLogger(SERVER_LOGGER)

    api_dir = os.path.dirname(os.path.abspath(api.__file__))
    for version in os.listdir(api_dir):
        version_dir = os.path.join(api_dir, version)
        version_dir = PurePosixPath(version_dir)
        if os.path.isdir(version_dir.as_posix()) and version_dir.stem.startswith('__') == False:
            for blueprint in os.listdir(version_dir):
                blueprint_dir = os.path.join(version_dir, blueprint)
                blueprint_dir = PurePosixPath(blueprint_dir)
                if os.path.isdir(blueprint_dir.as_posix()) and blueprint_dir.stem.startswith('__') == False:
                    for sub_router in os.listdir(blueprint_dir):
                        sub_router_dir = os.path.join(blueprint_dir, sub_router)
                        sub_router_dir = PurePosixPath(sub_router_dir)
                        if os.path.isdir(sub_router_dir.as_posix()) and sub_router_dir.stem.startswith('__') == False:
                            for file in os.listdir(sub_router_dir):
                                if file == 'api.py':
                                    logger.info(f"[api] - application.api.{version}.{blueprint}.{sub_router}.api is loaded")
                                    importlib.import_module(f"application.api.{version}.{blueprint}.{sub_router}.api")
                                    break
                                else:
                                    continue

def autodiscover_exceptions():
    logger = logging.getLogger(SERVER_LOGGER)

    api_dir = os.path.dirname(os.path.abspath(api.__file__))
    for version in os.listdir(api_dir):
        version_dir = os.path.join(api_dir, version)
        version_dir = PurePosixPath(version_dir)
        if os.path.isdir(version_dir.as_posix()) and version_dir.stem.startswith('__') == False:
            for blueprint in os.listdir(version_dir):
                blueprint_dir = os.path.join(version_dir, blueprint)
                blueprint_dir = PurePosixPath(blueprint_dir)
                if os.path.isdir(blueprint_dir.as_posix()) and blueprint_dir.stem.startswith('__') == False:
                    for sub_router in os.listdir(blueprint_dir):
                        sub_router_dir = os.path.join(blueprint_dir, sub_router)
                        sub_router_dir = PurePosixPath(sub_router_dir)
                        if os.path.isdir(sub_router_dir.as_posix()) and sub_router_dir.stem.startswith('__') == False:
                            for file in os.listdir(sub_router_dir):
                                if file == 'handler.py':
                                    logger.info(f"[exceptions] - application.api.{version}.{blueprint}.{sub_router}.handler is loaded")
                                    importlib.import_module(f"application.api.{version}.{blueprint}.{sub_router}.handler")
                                    break
                                else:
                                    continue