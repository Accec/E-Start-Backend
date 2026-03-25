from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

from core.api_schema import ArgsInvalidResponse, ErrorResponse, RateLimitResponse, RequestErrorResponse, SuccessResponse
from core.responses import InvalidCredentialsError, UserAlreadyExistsError
from ..common import validate_account_value, validate_password_value


class LoginBody(BaseModel):
    account: str = Field(min_length=5, max_length=30)
    password: str = Field(min_length=8, max_length=20)
    verify_code: Optional[str] = Field(default=None, min_length=8, max_length=20)


class RegisterBody(BaseModel):
    account: str = Field(min_length=5, max_length=20)
    password: str = Field(min_length=8, max_length=20)
    verify_code: Optional[str] = Field(default=None, min_length=6, max_length=6)

    @field_validator("account")
    @classmethod
    def check_account(cls, value):
        return validate_account_value(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return validate_password_value(value)


class LoginResponse(SuccessResponse):
    token: str


class RegisterResponse(SuccessResponse):
    result: Optional[Union[dict, list, str]] = Field(default=None)


class InvalidCredentialsResponse(ErrorResponse):
    code: int = Field(default=InvalidCredentialsError.code)
    msg: str = Field(default=InvalidCredentialsError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)


class AccountAlreadyExistsResponse(ErrorResponse):
    code: int = Field(default=UserAlreadyExistsError.code)
    msg: str = Field(default=UserAlreadyExistsError.msg)
    result: Optional[Union[dict, list, str]] = Field(default=None)
