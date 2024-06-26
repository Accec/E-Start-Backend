from pydantic import BaseModel, Field, field_validator
import datetime
from typing import Union, Optional, List
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class AdminGetLogsQuery(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    api: Optional[str] = None
    action: Optional[str] = None
    ip: Optional[str] = None
    ua: Optional[str] = None
    level: Optional[int] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20

    @field_validator('create_time', 'update_time', mode="before")
    def format_datetime_to_str(cls, value: datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None

class AdminGetLogModel(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    api: Optional[str] = None
    action: Optional[str] = None
    ip: Optional[str] = None
    ua: Optional[str] = None
    level: Optional[int] = None
    update_time: Optional[str] = None
    create_time: Optional[str] = None

    @field_validator('create_time', 'update_time', mode="before")
    def format_datetime_to_str(cls, value: datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class PaginatorSettings(BaseModel):
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminGetLogsSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[List[AdminGetLogModel]] = Field(default=None)
    total_items: int
    total_pages: int

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