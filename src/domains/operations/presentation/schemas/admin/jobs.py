from typing import Dict, Optional

from pydantic import BaseModel, Field

from core.api_schema import (
    ArgsInvalidResponse,
    AuthorizedErrorResponse,
    RateLimitResponse,
    RequestErrorResponse,
    SuccessResponse,
    TokenExpiredResponse,
)


class JobDetails(BaseModel):
    job_type: str
    interval: Optional[int] = None
    cron: Optional[str] = None
    status: int


class UpdateJobBody(BaseModel):
    job_name: str = Field()
    interval: Optional[int] = Field(default=None)
    cron: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)


class JobListResponse(SuccessResponse):
    result: Optional[Dict[str, JobDetails]] = Field(default=None)


class UpdateJobResponse(SuccessResponse):
    result: Optional[dict] = Field(default=None)
