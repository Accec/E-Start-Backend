from utils.constant import JOB_LOGGER
import logging

import sanic
import scheduler
import config

from models import Endpoint

Config = config.Config()
Server = sanic.Sanic.get_app(Config.APP)
Scheduler = scheduler.Scheduler()
Logger = logging.getLogger(JOB_LOGGER)


@Scheduler.add_job("update_endpoint", 1*60*60*24)
async def update_endpoint():
    routers = []
    for router in Server.router.groups.values():
        for method in router.methods:
            endpoint = {"endpoint": router.path, "method": method}
            routers.append(endpoint)

    for router in routers:
        if not await Endpoint.exists(**router):
            await Endpoint.create(**router)

    for record in await Endpoint.all():
        router = {"endpoint": record.endpoint, "method": record.method}
        if router not in routers:
            await record.delete()