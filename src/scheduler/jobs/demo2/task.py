import scheduler
Scheduler = scheduler.Scheduler()

@Scheduler.add_job("job_demo_2", 20)
async def demo2():
    Scheduler.logger.info("demo[2] running")