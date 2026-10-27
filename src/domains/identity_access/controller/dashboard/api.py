from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import Response
from core.http import schema_response
from domains.identity_access.services.dashboard import DashboardService

from infra.web.routing import add_route

from . import schemas
from ..support import schema_from, schema_list_from


@dataclass(slots=True)
class DashboardController:
    dashboard_service: DashboardService

    async def show_dashboard(self, request: Request):
        user_id = request.ctx.user["user_id"]
        user, roles, permissions, endpoints = await self.dashboard_service.get_dashboard(user_id=user_id)

        permission_models = schema_list_from(permissions, schemas.DashboardPermission)
        endpoint_models = schema_list_from(endpoints, schemas.DashboardEndpoint)
        user_model = schema_from(user, schemas.DashboardUser)
        role_models = schema_list_from(roles, schemas.DashboardRole)

        result = schemas.DashboardPayload(
            user_info=user_model,
            roles=role_models,
            endpoints=endpoint_models,
            permissions=permission_models,
        )
        return schema_response(Response(results=result), status=200)


def register_routes(user_blueprint, *, dashboard_service, jwt_auth):
    controller = DashboardController(dashboard_service=dashboard_service)

    add_route(
        user_blueprint,
        "/dashboard",
        methods=["GET"],
        handler=controller.show_dashboard,
        authorize=True,
        jwt_auth=jwt_auth,
    )
