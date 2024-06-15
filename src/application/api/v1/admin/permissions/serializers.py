from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional, List, Any
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class PermissionsModel(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None

class AdminPostPermissionsBody(BaseModel):
    permission_title: Optional[str] = None

class AdminPutPermissionsBody(BaseModel):
    id: Optional[int]
    permission_title: Optional[str]

class AdminGetPermissionsQuery(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminDeletePermissionsBody(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None

class PaginatorSettings(BaseModel):
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminGetPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[PermissionsModel, list]] = Field(default=None)
    total_items: int
    total_pages: int

class AdminPostPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[PermissionsModel, list]] = Field(default=None)

class AdminDeletePermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[PermissionsModel, list]] = Field(default=None)

class AdminPutPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[PermissionsModel, list]] = Field(default=None)

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