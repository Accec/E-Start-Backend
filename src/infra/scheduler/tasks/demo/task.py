import asyncio
import logging

from core.constants import TASK_DEMO, TASK_LOGGER
from infra.scheduler import add_task


Logger = logging.getLogger(TASK_LOGGER)


@add_task(TASK_DEMO)
async def demo():
    Logger.info("task: do something")
    await asyncio.sleep(10)
    Logger.info("task: done")
