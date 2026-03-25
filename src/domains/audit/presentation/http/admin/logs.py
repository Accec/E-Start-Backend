from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from core.http import schema_response
from domains.audit.domain import AuditLogQuery

from ...schemas.admin import logs as schemas


@dataclass(slots=True)
class AuditLogController:
    audit_service: object

    async def list_logs(self, request: Request, query: schemas.AuditLogListQuery):
        audit_query = AuditLogQuery(**query.model_dump(exclude_none=True))
        log_page = await self.audit_service.list_logs(audit_query)

        result = [schemas.AuditLogItem.model_validate(item, from_attributes=True) for item in log_page.items]
        return schema_response(
            schemas.AuditLogListResponse(
                result=result,
                total_items=log_page.total_items,
                total_pages=log_page.total_pages,
            ),
            status=200,
        )


def register_routes(admin_blueprint, audit_bootstrap, jwt_auth):
    controller = AuditLogController(audit_service=audit_bootstrap.audit_log_service)

    add_route(
        admin_blueprint,
        "/logs",
        methods=["GET"],
        handler=controller.list_logs,
        query=schemas.AuditLogListQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
