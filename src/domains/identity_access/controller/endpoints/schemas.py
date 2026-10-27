from typing import List, Optional

from pydantic import BaseModel

from core.api_schema import ArgsInvalidResponse, PaginatorSettings, TimestampedSchema
from ..common import PermissionRef


PermissionSummary = PermissionRef


class EndpointSummary(TimestampedSchema):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    permissions: Optional[List[PermissionSummary]] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None


class GetEndpointQuery(PaginatorSettings):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class PostEndpointPermissionBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permission: Optional[PermissionSummary] = None


class DeleteEndpointPermissionBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permission: Optional[PermissionSummary] = None
