import re
from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, UserExistError
from sanic_ext.exceptions import ValidationError

class PostRegisterBody(BaseModel):
    account: str = Field(min_length=5, max_length=20)
    password: str = Field(min_length=8, max_length=20)
    verify_code: Optional[str] = Field(default=None, min_length=6, max_length=6)

    @field_validator('account')
    @classmethod
    def check_account(cls, value):
        if not re.match("^[a-zA-Z0-9]+$", value):
            raise ValidationError(message="Account should only contain alphanumeric characters.")
        return value

    @field_validator('password')
    @classmethod
    def check_passowrd(cls, value):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,15}$', value):
            raise ValidationError(message="Password must be 8-15 characters long, include at least one uppercase letter, one lowercase letter, one number, and one special character.")
        return value

class UserExistResponse(BaseModel):
    code: int = Field(default=UserExistError.code)
    msg: str = Field(default=UserExistError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class SuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RequestErrorResponse(BaseModel):
    code: int = Field(default=RequestError.code)
    msg: str = Field(default=RequestError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class ArgsInvalidResponse(BaseModel):
    code: int = Field(default=ArgsInvalidError.code)
    msg: str = Field(default=ArgsInvalidError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RateLimitResponse(BaseModel):
    code: int = Field(default=RateLimitError.code)
    msg: str = Field(default=RateLimitError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)