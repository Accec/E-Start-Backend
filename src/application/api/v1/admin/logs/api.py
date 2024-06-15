from utils.router import AdminBlueprint
from utils.util import http_response

from sanic.request import Request
from sanic_ext import validate

from . import serializers
from models import Log

from modules.auth import jwt

from utils.util import Paginator

JwtAuth = jwt.JwtAuth()

@AdminBlueprint.get("/logs")
@validate(query=serializers.AdminGetLogsQuery)
@JwtAuth.permissions_authorized()
async def admin_get_logs(request: Request, query: serializers.AdminGetLogsQuery):
    log = serializers.AdminGetLogModel.model_validate(query, from_attributes=True)
    log = log.model_dump(exclude_none = True)
    paginator_settings = serializers.PaginatorSettings().model_validate(query, from_attributes=True)
    if log:
        paginator = Paginator(Log.filter(**log).all(), page_size=paginator_settings.page_size)
    else:
        paginator = Paginator(Log.all(), page_size=paginator_settings.page_size)

    await paginator.paginate(paginator_settings.page)
    result = [serializers.AdminGetLogModel.model_validate(item, from_attributes=True) for item in paginator.items]
    response = serializers.AdminGetLogsSuccessfullyResponse(result=result, total_items=paginator.total_items, total_pages=paginator.total_pages).model_dump()

    return http_response(status = 200, **response)