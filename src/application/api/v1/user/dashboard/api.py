from utils.response import Successfully
from utils.router import UserBlueprint
from utils.util import http_response
from sanic_ext import validate, openapi
from sanic_ext import serializer

from . import serializers


@UserBlueprint.post("/dashboard")
@openapi.summary("Dashboard")
@openapi.description("Dashboard")

async def post_dashboard(request):

    return http_response(Successfully.code, Successfully.msg)