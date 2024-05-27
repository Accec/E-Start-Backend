from utils.router import AdminBlueprint
from utils.util import http_response
from utils.response import Successfully, ArgsInvalidError, RateLimitError
from utils.constant import API_LOGGER

from sanic.request import Request
from sanic_ext import validate, openapi

import logging
import config
import scheduler
from utils import redis_conn

from . import serializers
from models import User, Log, Role

from modules.rate_limit import rate_limit
from modules.encryptor import hash_password
from modules.auth import jwt

JwtAuth = jwt.JwtAuth()

Scheduler = scheduler.Scheduler()
Logger = logging.getLogger(API_LOGGER)

@AdminBlueprint.get("/jobs")
@openapi.summary("Jobs")
@openapi.description("Jobs")
@openapi.secured("token")
@openapi.response(status=200, content={"application/json": serializers.AdminGetJobsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@JwtAuth.permissions_authorized()
async def admin_get_jobs(request: Request):
    job_list = await Scheduler.get_jobs()
    response = serializers.AdminGetJobsSuccessfullyResponse(result = job_list).model_dump()
    return http_response(status = 200, **response)

@AdminBlueprint.put("/jobs")
@openapi.summary("Jobs")
@openapi.description("Jobs")
@openapi.secured("token")
@openapi.body({"application/json": serializers.AdminPutJobsBody.model_json_schema()})
@openapi.response(status=200, content={"application/json": serializers.AdminPutJobsSuccessfullyResponse.model_json_schema()}, description="Successfully")
@openapi.response(status=400, content={"application/json": serializers.ArgsInvalidResponse.model_json_schema()}, description="Args invalid")
@openapi.response(status=401, content={"application/json": serializers.TokenExpiedResponse.model_json_schema()}, description="Token expied")
@openapi.response(status=403, content={"application/json": serializers.AuthorizedErrorResponse.model_json_schema()}, description="Authorized error")
@openapi.response(status=500, content={"application/json": serializers.RequestErrorResponse.model_json_schema()}, description="Request error")
@openapi.response(status=429, content={"application/json": serializers.RateLimitResponse.model_json_schema()}, description="Rate limit")
@validate(json=serializers.AdminPutJobsBody)
@JwtAuth.permissions_authorized()
async def admin_put_jobs(request: Request, body: serializers.AdminPutJobsBody):
    jobs = await Scheduler.get_jobs()
    if body.job_name not in jobs:
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    if not await Scheduler.set_job(**body.model_dump(exclude_none=True)):
        response = serializers.ArgsInvalidResponse().model_dump()
        return http_response(status = 400, **response)
    
    response = serializers.AdminPutJobsSuccessfullyResponse().model_dump()
    return http_response(status = 201, **response)