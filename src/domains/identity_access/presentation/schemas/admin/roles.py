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
from ..common import PermissionRef, RoleRef


PermissionSummary = PermissionRef


class AssignRolePermissionBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class RemoveRolePermissionBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class UpdateRoleBody(BaseModel):
    id: Optional[int]
    role_name: Optional[str]


class RoleListQuery(PaginatorSettings):
    id: Optional[int] = None
    role_name: Optional[str] = None


class CreateRoleBody(BaseModel):
    role_name: str


class DeleteRoleBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None


class RoleSummary(RoleRef):
    permissions: Optional[List[PermissionSummary]] = None


class RoleListResponse(PaginatedResponse):
    result: Optional[List[RoleSummary]] = Field(default=None)


class CreateRoleResponse(SuccessResponse):
    pass


class AssignRolePermissionResponse(SuccessResponse):
    pass


class RemoveRolePermissionResponse(SuccessResponse):
    pass


class DeleteRoleResponse(SuccessResponse):
    pass


class UpdateRoleResponse(SuccessResponse):
    pass
