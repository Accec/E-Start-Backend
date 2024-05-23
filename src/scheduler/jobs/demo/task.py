import scheduler
Scheduler = scheduler.Scheduler()

@Scheduler.add_job("job_demo", 10)
async def demo():
    Scheduler.logger.info("demo running")