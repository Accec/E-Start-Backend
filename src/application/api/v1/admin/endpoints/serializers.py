from pydantic import BaseModel, Field, field_validator
import datetime
from typing import Union, Optional, List, Any
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class PermissionsModel(BaseModel):
    id: Optional[int] = None
    permission_title: Optional[str] = None

class EndpointsModel(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    permissions: Optional[Any] = []
    update_time: Optional[str] = None
    create_time: Optional[str] = None

    @field_validator('create_time', 'update_time', mode="before")
    def format_datetime_to_str(cls, value: datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None

class AdminGetEndpointsQuery(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminPostEndpointsPermissionsBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permissions: Optional[PermissionsModel] = None

class AdminDeleteEndpointsPermissionsBody(BaseModel):
    id: Optional[int] = None
    endpoint: Optional[str] = None
    permissions: Optional[PermissionsModel] = None

class PermissionsModel(BaseModel):
    id: int = None
    permission_title: str = None

class PaginatorSettings(BaseModel):
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminGetEndpointsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[list, List[EndpointsModel]]]
    total_items: int
    total_pages: int

class AdminPostEndpointsPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[list, List[EndpointsModel]]]

class AdminDeleteEndpointsPermissionsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[list, List[EndpointsModel]]]

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