from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from core.http import schema_response
from core.responses import InvalidArgumentsError
from domains.operations.domain import SchedulerJobUpdate

from ...schemas.admin import jobs as schemas


def bad_request_response():
    return schema_response(
        schemas.ArgsInvalidResponse(code=InvalidArgumentsError.code, msg=InvalidArgumentsError.msg),
        status=400,
    )


@dataclass(slots=True)
class SchedulerJobsController:
    job_service: object

    async def list_jobs(self, request: Request):
        job_list = await self.job_service.get_jobs()
        return schema_response(
            schemas.JobListResponse(result={name: job.to_mapping() for name, job in job_list.items()}),
            status=200,
        )

    async def update_job(self, request: Request, body: schemas.UpdateJobBody):
        jobs = await self.job_service.get_jobs()
        if body.job_name not in jobs:
            return bad_request_response()

        update = SchedulerJobUpdate(**body.model_dump(exclude_none=True))
        if not await self.job_service.update_job(update):
            return bad_request_response()

        return schema_response(schemas.UpdateJobResponse(), status=201)


def register_routes(admin_blueprint, operations_bootstrap, jwt_auth):
    controller = SchedulerJobsController(job_service=operations_bootstrap.scheduler_job_service)

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
        json=schemas.UpdateJobBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
