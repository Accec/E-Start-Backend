from pydantic import BaseModel, Field
from typing import Union, Optional
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class SuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RequestErrorResponse(BaseModel):
    code: int = Field(default=RequestError.code)
    msg: str = Field(default=RequestError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class TokenExpiedResponse(BaseModel):
    code: int = Field(default=TokenError.code)
    msg: str = Field(default=TokenError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class AuthorizedErrorResponse(BaseModel):
    code: int = Field(default=AuthorizedError.code)
    msg: str = Field(default=AuthorizedError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class ArgsInvalidResponse(BaseModel):
    code: int = Field(default=ArgsInvalidError.code)
    msg: str = Field(default=ArgsInvalidError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RateLimitResponse(BaseModel):
    code: int = Field(default=RateLimitError.code)
    msg: str = Field(default=RateLimitError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)