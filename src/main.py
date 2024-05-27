import config
from utils.logger import Logger
from utils.create_app import create_app


from utils.constant import API_LOGGER, TASK_LOGGER, JOB_LOGGER, SERVER_LOGGER, SCHEDULER_LOGGER

Config = config.Config()
Server = create_app()

Logger.setupLogger(SERVER_LOGGER)
Logger.setupLogger(SCHEDULER_LOGGER)
Logger.setupLogger(API_LOGGER)
Logger.setupLogger(TASK_LOGGER)
Logger.setupLogger(JOB_LOGGER)

import asyncio
import sys
import logging

import scheduler

from modules.auth import jwt
from utils import redis_conn
from utils import cli

Logging = logging.getLogger(SERVER_LOGGER)
JwtAuth = jwt.JwtAuth(Config.JwtSecretKey)
RedisConn = redis_conn.RedisClient(Config.RedisUrl)
Scheduler = scheduler.Scheduler(RedisConn)

 
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli.cli()

from utils import router

"""
@Server.main_process_start
async def start_scheduler(app, loop):
    Logging.info("Start the service")
    Scheduler.run_by_thread()

@Server.main_process_stop
async def stop_scheduler(app, loop):
    
    await asyncio.sleep(0.1)
    await Scheduler.shutdown()
    await asyncio.get_event_loop().shutdown_asyncgens()

    Logging.info("Stop the service")
"""

@Server.after_server_start
async def start_scheduler(app, loop):
    Logging.info("Start the service")
    app.add_task(Scheduler.run_by_async)

@Server.before_server_stop
async def stop_scheduler(app, loop):
    
    await asyncio.sleep(0.1)
    await Scheduler.shutdown()
    await asyncio.get_event_loop().shutdown_asyncgens()

    Logging.info("Stop the service")
    
from middleware.request_handling.request_handling import request_handling

Server.middleware(request_handling)

for bp in router.Blueprints:
    Logging.info(f"[Blueprint] - [{bp.name}] is loaded")
    Server.blueprint(bp)

if __name__ == "__main__":
    Server.run(host = Config.SanicHost, port = Config.SanicPort, debug = Config.DeBug, access_log = False, single_process=True)