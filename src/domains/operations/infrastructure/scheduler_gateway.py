from ..domain import SchedulerJobUpdate


class SchedulerGateway:
    def __init__(self, *, scheduler):
        self.scheduler = scheduler

    async def get_jobs(self):
        return await self.scheduler.get_jobs()

    async def update_job(self, update: SchedulerJobUpdate):
        return await self.scheduler.set_job(**update.to_mapping())
