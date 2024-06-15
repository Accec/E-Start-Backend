from utils.router import AdminBlueprint
from utils.util import http_response
from utils.constant import API_LOGGER
from utils.constant import LogLevel

from sanic.request import Request
from sanic_ext import validate

import logging
import scheduler
from . import serializers

from modules.auth import jwt

JwtAuth = jwt.JwtAuth()

Scheduler = scheduler.Scheduler()
Logger = logging.getLogger(API_LOGGER)

@AdminBlueprint.get("/jobs")
@JwtAuth.permissions_authorized()
async def admin_get_jobs(request: Request):
    job_list = await Scheduler.get_jobs()
    response = serializers.AdminGetJobsSuccessfullyResponse(result = job_list).model_dump()
    return http_response(status = 200, **response)

@AdminBlueprint.put("/jobs")
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