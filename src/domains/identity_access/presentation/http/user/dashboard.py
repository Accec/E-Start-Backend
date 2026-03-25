from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route

from ...schemas.user import dashboard as schemas
from ..support import response_from, schema_from, schema_list_from


@dataclass(slots=True)
class DashboardController:
    dashboard_service: object

    async def show_dashboard(self, request: Request):
        user_id = request.ctx.user["user_id"]
        user, roles, permissions, endpoints = await self.dashboard_service.get_dashboard(user_id)

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
        return response_from(schemas.DashboardResponse(result=result), status=200)


def register_routes(user_blueprint, identity_access):
    controller = DashboardController(dashboard_service=identity_access.dashboard_service)

    add_route(
        user_blueprint,
        "/dashboard",
        methods=["GET"],
        handler=controller.show_dashboard,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
