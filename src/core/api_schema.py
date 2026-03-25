import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .responses import (
    InvalidArgumentsError,
    PermissionDeniedError,
    RequestError,
    Success,
    TokenExpiredError,
    TooManyRequestsError,
)


class SchemaModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(SchemaModel):
    @field_validator("create_time", "update_time", mode="before", check_fields=False)
    @classmethod
    def format_datetime_to_str(cls, value):
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value


class PaginatorSettings(SchemaModel):
    page: int = Field(default=1)
    page_size: int = Field(default=20)


class SuccessResponse(SchemaModel):
    code: int = Field(default=Success.code)
    msg: str = Field(default=Success.msg)
    result: Optional[Any] = Field(default=None)


class PaginatedResponse(SuccessResponse):
    total_items: int
    total_pages: int


class ErrorResponse(SchemaModel):
    code: int
    msg: str
    result: Optional[Union[dict, list, str]] = Field(default=None)


class RequestErrorResponse(ErrorResponse):
    code: int = Field(default=RequestError.code)
    msg: str = Field(default=RequestError.msg)


class TokenExpiredResponse(ErrorResponse):
    code: int = Field(default=TokenExpiredError.code)
    msg: str = Field(default=TokenExpiredError.msg)


class AuthorizedErrorResponse(ErrorResponse):
    code: int = Field(default=PermissionDeniedError.code)
    msg: str = Field(default=PermissionDeniedError.msg)


class ArgsInvalidResponse(ErrorResponse):
    code: int = Field(default=InvalidArgumentsError.code)
    msg: str = Field(default=InvalidArgumentsError.msg)


class RateLimitResponse(ErrorResponse):
    code: int = Field(default=TooManyRequestsError.code)
    msg: str = Field(default=TooManyRequestsError.msg)
