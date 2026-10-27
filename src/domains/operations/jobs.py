from dataclasses import dataclass


INTERVAL_JOB_TYPE = "interval"
CRON_JOB_TYPE = "cron"
JOB_STATUS_PAUSED = 0
JOB_STATUS_RUNNING = 1


@dataclass(frozen=True, slots=True)
class SchedulerJob:
    name: str
    job_type: str
    interval: int | None = None
    cron: str | None = None
    status: int = JOB_STATUS_RUNNING

    @classmethod
    def from_mapping(cls, name: str, payload: dict):
        job = cls(
            name=name,
            job_type=str(payload["job_type"]),
            interval=int(payload["interval"]) if payload.get("interval") is not None else None,
            cron=payload.get("cron"),
            status=int(payload["status"]),
        )
        job.validate()
        return job

    def validate(self):
        if self.job_type not in {INTERVAL_JOB_TYPE, CRON_JOB_TYPE}:
            raise ValueError(f"Unsupported job type: {self.job_type}")
        if self.status not in {JOB_STATUS_PAUSED, JOB_STATUS_RUNNING}:
            raise ValueError(f"Unsupported job status: {self.status}")
        if self.job_type == INTERVAL_JOB_TYPE:
            if self.interval is None or self.interval < 1:
                raise ValueError("Interval jobs require a positive interval")
            if self.cron is not None:
                raise ValueError("Interval jobs cannot define a cron expression")
        if self.job_type == CRON_JOB_TYPE and self.interval is not None:
            raise ValueError("Cron jobs cannot define an interval")

    def to_mapping(self):
        return {
            "job_type": self.job_type,
            "interval": self.interval,
            "cron": self.cron,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class SchedulerJobUpdate:
    job_name: str
    interval: int | None = None
    cron: str | None = None
    status: int | None = None

    def validate_against(self, job: SchedulerJob):
        if self.status is not None and self.status not in {JOB_STATUS_PAUSED, JOB_STATUS_RUNNING}:
            raise ValueError(f"Unsupported job status: {self.status}")
        if job.job_type == INTERVAL_JOB_TYPE:
            if self.cron is not None:
                raise ValueError("Interval jobs cannot be updated with a cron expression")
            if self.interval is not None and self.interval < 1:
                raise ValueError("Interval jobs require a positive interval")
        if job.job_type == CRON_JOB_TYPE and self.interval is not None:
            raise ValueError("Cron jobs cannot be updated with an interval")

    def to_mapping(self):
        payload = {"job_name": self.job_name}
        if self.interval is not None:
            payload["interval"] = self.interval
        if self.cron is not None:
            payload["cron"] = self.cron
        if self.status is not None:
            payload["status"] = self.status
        return payload
