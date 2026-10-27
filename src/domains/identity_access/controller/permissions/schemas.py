from typing import Optional

from pydantic import BaseModel

from core.api_schema import ArgsInvalidResponse, PaginatorSettings
from ..common import PermissionRef


PermissionSummary = PermissionRef


class PostPermissionBody(BaseModel):
    permission_title: Optional[str] = None


class PutPermissionBody(BaseModel):
    id: Optional[int]
    permission_title: Optional[str]


class GetPermissionQuery(PaginatorSettings):
    id: Optional[int] = None
    permission_title: Optional[str] = None


class DeletePermissionBody(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None
