from pydantic import BaseModel, Field
from typing import Union, Optional, Dict, List
from utils.response import Successfully, ArgsInvalidError, RateLimitError, RequestError, TokenError, AuthorizedError

class UserGetDashboardUserModel(BaseModel):
    id: int
    account: str
    open_id: str
    status: int

class UserGetDashboardRolesModel(BaseModel):
    id: int
    role_name: str

class UserGetDashboardPermissionsModel(BaseModel):
    id: int
    permission_title: str

class UserGetDashboardEndpointsModel(BaseModel):
    id: int
    method: str
    endpoint: str

class UserGetDashboardResultsModel(BaseModel):
    user_info: UserGetDashboardUserModel
    roles: List[UserGetDashboardRolesModel]
    permissions: List[UserGetDashboardPermissionsModel]
    endpoints: List[UserGetDashboardEndpointsModel]

class UserGetDashboardSuccessfullyResponse(BaseModel):
    code: int = Field(default=Successfully.code)
    msg: str = Field(default=Successfully.msg)
    results: Optional[Union[UserGetDashboardResultsModel]]

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