from utils.constant import TASK_DEMO

import scheduler
Scheduler = scheduler.Scheduler()

@Scheduler.add_task(TASK_DEMO)
async def demo():
    Scheduler.logger.info("task: do somethings")