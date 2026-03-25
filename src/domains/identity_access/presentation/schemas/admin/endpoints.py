from typing import List, Optional

from pydantic import BaseModel
from pydantic import Field

from core.api_schema import (
    ArgsInvalidResponse,
    AuthorizedErrorResponse,
    PaginatorSettings,
    PaginatedResponse,
    RateLimitResponse,
    RequestErrorResponse,
    SuccessResponse,
    TimestampedSchema,
    TokenExpiredResponse,
)
from ..common import PermissionRef


PermissionSummary = PermissionRef


class EndpointSummary(TimestampedSchema):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    permissions: Optional[List[PermissionSummary]] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None


class EndpointListQuery(PaginatorSettings):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class AssignEndpointPermissionBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class RemoveEndpointPermissionBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class EndpointListResponse(PaginatedResponse):
    result: Optional[List[EndpointSummary]] = Field(default=None)


class AssignEndpointPermissionResponse(SuccessResponse):
    pass


class RemoveEndpointPermissionResponse(SuccessResponse):
    pass
