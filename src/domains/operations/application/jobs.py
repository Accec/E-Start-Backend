from ..domain import SchedulerJob, SchedulerJobUpdate
from .ports import SchedulerJobsPort


class SchedulerJobService:
    def __init__(self, *, jobs: SchedulerJobsPort):
        self.jobs = jobs

    async def get_jobs(self):
        raw_jobs = await self.jobs.get_jobs()
        return {
            name: SchedulerJob.from_mapping(name, payload)
            for name, payload in raw_jobs.items()
        }

    async def update_job(self, update: SchedulerJobUpdate):
        jobs = await self.get_jobs()
        job = jobs.get(update.job_name)
        if job is None:
            return False

        try:
            update.validate_against(job)
        except ValueError:
            return False

        return await self.jobs.update_job(update)
