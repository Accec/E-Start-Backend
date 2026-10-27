from typing import Optional

from pydantic import BaseModel, Field

from core.api_schema import ArgsInvalidResponse


class JobDetails(BaseModel):
    job_type: str
    interval: Optional[int] = None
    cron: Optional[str] = None
    status: int


class PutJobBody(BaseModel):
    job_name: str = Field()
    interval: Optional[int] = Field(default=None)
    cron: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)
