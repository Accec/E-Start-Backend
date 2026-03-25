from typing import List, Optional

from pydantic import BaseModel, Field

from core.api_schema import (
    ArgsInvalidResponse,
    AuthorizedErrorResponse,
    PaginatorSettings,
    PaginatedResponse,
    RateLimitResponse,
    RequestErrorResponse,
    SuccessResponse,
    TokenExpiredResponse,
)
from ..common import PermissionRef


PermissionSummary = PermissionRef


class CreatePermissionBody(BaseModel):
    permission_title: Optional[str] = None


class UpdatePermissionBody(BaseModel):
    id: Optional[int]
    permission_title: Optional[str]


class PermissionListQuery(PaginatorSettings):
    id: Optional[int] = None
    permission_title: Optional[str] = None


class DeletePermissionBody(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None


class PermissionListResponse(PaginatedResponse):
    result: Optional[List[PermissionSummary]] = Field(default=None)


class CreatePermissionResponse(SuccessResponse):
    pass


class DeletePermissionResponse(SuccessResponse):
    pass


class UpdatePermissionResponse(SuccessResponse):
    pass
