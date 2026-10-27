from dataclasses import dataclass

from sanic.request import Request

from infra.web.routing import add_route
from core.api_schema import Response
from core.http import schema_response
from domains.operations.services.jobs import SchedulerJobService
from core.responses import InvalidArgumentsError

from . import schemas


def bad_request_response():
    return schema_response(
        schemas.ArgsInvalidResponse(code=InvalidArgumentsError.code, msg=InvalidArgumentsError.msg),
        status=400,
    )


@dataclass(slots=True)
class SchedulerJobsController:
    job_service: SchedulerJobService

    async def list_jobs(self, request: Request):
        job_list = await self.job_service.get_jobs()
        return schema_response(
            Response(results={
                name: schemas.JobDetails.model_validate(job.to_mapping())
                for name, job in job_list.items()
            }),
            status=200,
        )

    async def update_job(self, request: Request, body: schemas.PutJobBody):
        jobs = await self.job_service.get_jobs()
        if body.job_name not in jobs:
            return bad_request_response()

        if not await self.job_service.update_job(
            job_name=body.job_name,
            interval=body.interval,
            cron=body.cron,
            status=body.status,
        ):
            return bad_request_response()

        return schema_response(Response(), status=201)


def register_routes(admin_blueprint, *, job_service, jwt_auth):
    controller = SchedulerJobsController(job_service=job_service)

    add_route(
        admin_blueprint,
        "/jobs",
        methods=["GET"],
        handler=controller.list_jobs,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/jobs",
        methods=["PUT"],
        handler=controller.update_job,
        json=schemas.PutJobBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
