from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional, List, Any
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class PermissionsModel(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None

class AdminPostRolesPermissionsBody(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permissions: Optional[PermissionsModel] = None

class AdminPutRolesBody(BaseModel):
    id: Optional[int]
    role_name: Optional[str]

class AdminGetRolesQuery(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminPostRolesBody(BaseModel):
    role_name: str = None

class AdminDeleteRolesQuery(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None

class RolesModel(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None
    permissions: Optional[Any] = []

class PaginatorSettings(BaseModel):
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminGetRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)
    total_items: int
    total_pages: int

class AdminPostRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)

class AdminPostRolesPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)

class AdminDeleteRolesPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)


class AdminDeleteRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)

class AdminPutRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[RolesModel, list]] = Field(default=None)

class RequestErrorResponse(BaseModel):
    code: int = Field(default=RequestError.code)
    msg: str = Field(default=RequestError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)

class TokenExpiedResponse(BaseModel):
    code: int = Field(default=TokenError.code)
    msg: str = Field(default=TokenError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)

class AuthorizedErrorResponse(BaseModel):
    code: int = Field(default=AuthorizedError.code)
    msg: str = Field(default=AuthorizedError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)

class ArgsInvalidResponse(BaseModel):
    code: int = Field(default=ArgsInvalidError.code)
    msg: str = Field(default=ArgsInvalidError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)

class RateLimitResponse(BaseModel):
    code: int = Field(default=RateLimitError.code)
    msg: str = Field(default=RateLimitError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)