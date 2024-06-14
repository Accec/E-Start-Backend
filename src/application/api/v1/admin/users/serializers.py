from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional, List
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError
import re
from sanic_ext.exceptions import ValidationError

class RolesModel(BaseModel):
    id: Optional[int] = None
    role_name: Optional[str] = None

class UsersModel(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    open_id: Optional[str] = None
    roles: Optional[RolesModel] = None

class AdminGetUsersQuery(BaseModel):
    id: Optional[int] = Field(default=None)
    account: Optional[str]  = Field(default=None)
    page: Optional[int] = Field(default=1)
    page_size: Optional[int] = Field(default=20)

class AdminPostUsersBody(BaseModel):
    account: Optional[str] = Field(min_length=5, max_length=20)
    password: Optional[str] = Field(min_length=8, max_length=20)

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
    
class AdminPutUsersBody(BaseModel):
    account: Optional[str] = Field(min_length=5, max_length=20)
    password: Optional[str] = Field(min_length=8, max_length=20)

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
    
class AdminPostUsersRolesBody(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    roles: Optional[RolesModel] = None

class AdminDeleteUsersRolesBody(BaseModel):
    id: Optional[int] = None
    account: Optional[str] = None
    roles: Optional[RolesModel] = None

class PaginatorSettings(BaseModel):
    page: int = Field(default=1)
    page_size: int = Field(default=20)

class AdminGetUsersSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[List[UsersModel], list]] = Field(default=None)
    total_items: int
    total_pages: int

class AdminPostUsersSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[List[UsersModel], list]] = Field(default=None)

class AdminPutUsersSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[List[UsersModel], list]] = Field(default=None)

class AdminPostUsersRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[List[UsersModel], list]] = Field(default=None)

class AdminDeleteUsersRolesSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    result: Optional[Union[List[UsersModel], list]] = Field(default=None)

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