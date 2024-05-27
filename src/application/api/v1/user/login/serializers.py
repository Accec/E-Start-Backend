from pydantic import BaseModel, Field
from typing import Union, Optional
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, AccountOrPasswordInvalid

class PostLoginBody(BaseModel):
    account: str = Field(min_length=5, max_length=30)
    password: str = Field(min_length=8, max_length=20)
    verify_code: Optional[str] = Field(default=None, min_length=8, max_length=20)

class SuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RequestErrorResponse(BaseModel):
    code: int = Field(default=RequestError.code)
    msg: str = Field(default=RequestError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class AccountOrPasswordInvalidResponse(BaseModel):
    code: int = Field(default=AccountOrPasswordInvalid.code)
    msg: str = Field(default=AccountOrPasswordInvalid.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class ArgsInvalidResponse(BaseModel):
    code: int = Field(default=ArgsInvalidError.code)
    msg: str = Field(default=ArgsInvalidError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)

class RateLimitResponse(BaseModel):
    code: int = Field(default=RateLimitError.code)
    msg: str = Field(default=RateLimitError.msg)
    results: Optional[Union[dict, list, str]] = Field(default=None)