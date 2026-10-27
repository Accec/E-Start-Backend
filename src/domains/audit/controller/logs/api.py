from dataclasses import dataclass

from sanic.request import Request

from infra.web.routing import add_route
from core.api_schema import PaginatedResponse
from core.http import schema_response
from domains.audit.services.logs import AuditLogService

from . import schemas


@dataclass(slots=True)
class AuditLogController:
    audit_service: AuditLogService

    async def list_logs(self, request: Request, query: schemas.GetAuditLogQuery):
        log_page = await self.audit_service.list_logs(
            id=query.id,
            user_id=query.user_id,
            api=query.api,
            action=query.action,
            ip=query.ip,
            ua=query.ua,
            level=query.level,
            update_time=query.update_time,
            create_time=query.create_time,
            page=query.page,
            page_size=query.page_size,
        )

        result = [schemas.AuditLogItem.model_validate(item, from_attributes=True) for item in log_page.items]
        return schema_response(
            PaginatedResponse(
                results=result,
                total_items=log_page.total_items,
                total_pages=log_page.total_pages,
            ),
            status=200,
        )


def register_routes(admin_blueprint, *, audit_service, jwt_auth):
    controller = AuditLogController(audit_service=audit_service)

    add_route(
        admin_blueprint,
        "/logs",
        methods=["GET"],
        handler=controller.list_logs,
        query=schemas.GetAuditLogQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
