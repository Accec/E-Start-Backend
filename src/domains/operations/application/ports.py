from typing import Protocol

from ..domain import SchedulerJobUpdate


class SchedulerJobsPort(Protocol):
    async def get_jobs(self) -> dict[str, dict]: ...

    async def update_job(self, update: SchedulerJobUpdate) -> bool: ...


__all__ = ["SchedulerJobsPort"]
