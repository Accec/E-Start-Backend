from typing import List, Optional

from pydantic import BaseModel, Field

from core.api_schema import ArgsInvalidResponse, AuthorizedErrorResponse, RateLimitResponse, RequestErrorResponse, SuccessResponse, TokenExpiredResponse


class DashboardUser(BaseModel):
    id: int
    account: str
    open_id: str
    status: int


class DashboardRole(BaseModel):
    id: int
    role_name: str


class DashboardPermission(BaseModel):
    id: int
    permission_title: str


class DashboardEndpoint(BaseModel):
    id: int
    method: str
    endpoint: str


class DashboardPayload(BaseModel):
    user_info: DashboardUser
    roles: List[DashboardRole]
    permissions: List[DashboardPermission]
    endpoints: List[DashboardEndpoint]


class DashboardResponse(SuccessResponse):
    result: Optional[DashboardPayload] = Field(default=None)
