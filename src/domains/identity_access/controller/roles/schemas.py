from typing import List, Optional

from pydantic import BaseModel

from core.api_schema import ArgsInvalidResponse, PaginatorSettings
from ..common import PermissionRef, RoleRef


PermissionSummary = PermissionRef


class PostRolePermissionBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class DeleteRolePermissionBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class PutRoleBody(BaseModel):
    id: Optional[int]
    role_name: Optional[str]


class GetRoleQuery(PaginatorSettings):
    id: Optional[int] = None
    role_name: Optional[str] = None


class PostRoleBody(BaseModel):
    role_name: str


class DeleteRoleBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None


class RoleSummary(RoleRef):
    permissions: Optional[List[PermissionSummary]] = None
