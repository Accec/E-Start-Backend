from typing import List, Optional

from pydantic import Field

from core.api_schema import (
    ArgsInvalidResponse,
    AuthorizedErrorResponse,
    PaginatorSettings,
    PaginatedResponse,
    RateLimitResponse,
    RequestErrorResponse,
    TimestampedSchema,
    TokenExpiredResponse,
)


class AuditLogListQuery(PaginatorSettings):
    id: Optional[int] = None
    user_id: Optional[int] = None
    api: Optional[str] = None
    action: Optional[str] = None
    ip: Optional[str] = None
    ua: Optional[str] = None
    level: Optional[int] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None


class AuditLogItem(TimestampedSchema):
    id: Optional[int] = None
    user_id: Optional[int] = None
    api: Optional[str] = None
    action: Optional[str] = None
    ip: Optional[str] = None
    ua: Optional[str] = None
    level: Optional[int] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None


class AuditLogListResponse(PaginatedResponse):
    result: Optional[List[AuditLogItem]] = Field(default=None)
