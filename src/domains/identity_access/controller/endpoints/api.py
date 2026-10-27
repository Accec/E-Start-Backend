from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import PaginatedResponse, Response
from core.http import schema_response
from domains.identity_access.services.endpoints import EndpointAdminService

from infra.web.routing import add_route
from domains.identity_access.errors import RelationAlreadyExistsError, RelationNotFoundError, ResourceNotFoundError

from . import schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    schema_from,
)


@dataclass(slots=True)
class EndpointAdminController:
    endpoint_service: EndpointAdminService

    async def list_endpoints(self, request: Request, query: schemas.GetEndpointQuery):
        page_result = await self.endpoint_service.list_endpoints(
            endpoint_id=query.id,
            endpoint_path=query.endpoint,
            method=query.method,
            page=query.page,
            page_size=query.page_size,
        )
        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.EndpointSummary)
            permissions = [
                schema_from(permission, schemas.PermissionSummary) for permission in await item.permissions.all()
            ]
            result.permissions = permissions
            results.append(result)

        return schema_response(
            PaginatedResponse(
                results=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def assign_permission(self, request: Request, body: schemas.PostEndpointPermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.endpoint_service.add_permission(
                endpoint_id=body.id,
                endpoint_path=body.endpoint,
                permission_id=body.permission.id,
                permission_title=body.permission.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationAlreadyExistsError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def remove_permission(self, request: Request, body: schemas.DeleteEndpointPermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.endpoint_service.remove_permission(
                endpoint_id=body.id,
                endpoint_path=body.endpoint,
                permission_id=body.permission.id,
                permission_title=body.permission.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationNotFoundError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=204)


def register_routes(admin_blueprint, *, endpoint_service, jwt_auth):
    controller = EndpointAdminController(endpoint_service=endpoint_service)

    add_route(
        admin_blueprint,
        "/endpoints",
        methods=["GET"],
        handler=controller.list_endpoints,
        query=schemas.GetEndpointQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/endpoints/permissions",
        methods=["POST"],
        handler=controller.assign_permission,
        json=schemas.PostEndpointPermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/endpoints/permissions",
        methods=["DELETE"],
        handler=controller.remove_permission,
        json=schemas.DeleteEndpointPermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
