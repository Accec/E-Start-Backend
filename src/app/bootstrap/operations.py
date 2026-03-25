from dataclasses import dataclass

from domains.operations.application import SchedulerJobService
from domains.operations.infrastructure.scheduler_gateway import SchedulerGateway
from infra.scheduler import Scheduler


@dataclass(slots=True)
class OperationsBootstrap:
    scheduler: Scheduler
    scheduler_gateway: SchedulerGateway
    scheduler_job_service: SchedulerJobService


__all__ = ["OperationsBootstrap"]
