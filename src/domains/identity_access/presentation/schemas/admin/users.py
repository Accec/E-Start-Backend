from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

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
from ..common import RoleRef, validate_account_value, validate_password_value


RoleSummary = RoleRef


class UserSummary(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    open_id: Optional[str] = None
    status: Optional[int] = None
    roles: Optional[List[RoleSummary]] = None


class UserListQuery(PaginatorSettings):
    id: Optional[int] = Field(default=None)
    account: Optional[str] = Field(default=None)


class CreateUserBody(BaseModel):
    account: Optional[str] = Field(min_length=5, max_length=20)
    password: Optional[str] = Field(min_length=8, max_length=20)

    @field_validator("account")
    @classmethod
    def check_account(cls, value):
        return validate_account_value(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return validate_password_value(value)


class UpdateUserBody(CreateUserBody):
    id: Optional[int] = None


class AssignUserRoleBody(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    role: Optional[RoleSummary] = None


class RemoveUserRoleBody(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    role: Optional[RoleSummary] = None


class UserListResponse(PaginatedResponse):
    result: Optional[List[UserSummary]] = Field(default=None)


class CreateUserResponse(SuccessResponse):
    pass


class UpdateUserResponse(SuccessResponse):
    pass


class AssignUserRoleResponse(SuccessResponse):
    pass


class RemoveUserRoleResponse(SuccessResponse):
    pass
