import asyncio
from sanic.app import Sanic

from utils.create_app import create_app, load_task
import config
from utils import logger
import scheduler

from modules.auth import jwt
from utils import redis_conn

Config = config.Config()
Config = Config.load_config()
JwtAuth = jwt.JwtAuth(Config.JwtSecretKey)
RedisConn = redis_conn.RedisClient(Config.RedisUrl)

Server = create_app(Sanic("E-Starter"))

Logging = logger.Logger()
Scheduler = scheduler.Scheduler()

from utils import router

@Server.listener("before_server_start")
async def strart_scheduler(app, loop):
    Logging.info("Start the service")
    await Scheduler.init_loop()
    load_task()

Server.add_task(Scheduler.start_jobs())

@Server.listener("before_server_stop")
async def stop_scheduler(app, loop):
    await asyncio.sleep(0.1)
    await Scheduler.cancel_jobs()
    await asyncio.get_event_loop().shutdown_asyncgens()

    Logging.info("Stop the service")
    
from middleware.request_handling.request_handling import request_handling

Server.middleware(request_handling)

Server.blueprint(router.UserBlueprint)

if __name__ == "__main__":

    Server.run(host = Config.SanicHost, port = Config.SanicPort, debug = Config.DeBug, access_log = False)