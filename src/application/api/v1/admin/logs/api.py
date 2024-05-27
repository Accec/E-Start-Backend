from utils.router import AdminBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError

from sanic.request import Request
from sanic_ext import validate, openapi

from . import serializers
from models import User, Log, Role, Endpoint

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

from utils.util import Paginator
import asyncio

JwtAuth = jwt.JwtAuth()

@AdminBlueprint.get("/logs")
@openapi.summary("Retrieve system logs")
@openapi.description("This endpoint allows you to retrieve system logs based on specified criteria. It supports pagination and filtering.")
@openapi.secured("token")
@openapi.body(serializers.AdminGetLogsQuery, description="Filter settings to apply when retrieving logs.")
@openapi.response(status=200, content={"application/json": serializers.AdminGetLogsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(query=serializers.AdminGetLogsQuery)
@JwtAuth.permissions_authorized()
async def admin_get_logs(request: Request, query: serializers.AdminGetLogsQuery):
    log = serializers.AdminGetLogModel().model_validate(query, from_attributes=True)
    log = log.model_dump(exclude_none = True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if log:
        paginator = Paginator(Log.filter(**log).all(), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(Log.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    result = [serializers.AdminGetLogModel.model_validate(item, from_attributes=True) for item in paginator.items]
    response = serializers.AdminGetLogsSuccessfullyResponse(result=result).model_dump()

    return http_response(status = 200, **response)