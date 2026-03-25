from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from ....application.contracts import EndpointPermissionBinding
from ....domain import EndpointListQuery, EndpointReference, PermissionReference
from domains.identity_access.domain.errors import RelationAlreadyExistsError, RelationNotFoundError, ResourceNotFoundError

from ...schemas.admin import endpoints as schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    response_from,
    schema_from,
)


@dataclass(slots=True)
class EndpointAdminController:
    endpoint_service: object

    async def list_endpoints(self, request: Request, query: schemas.EndpointListQuery):
        endpoint_query = EndpointListQuery(
            endpoint_id=query.id,
            endpoint_path=query.endpoint,
            method=query.method,
            page=query.page,
            page_size=query.page_size,
        )
        page_result = await self.endpoint_service.list_endpoints(endpoint_query)

        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.EndpointSummary)
            permissions = [
                schema_from(permission, schemas.PermissionSummary) for permission in await item.permissions.all()
            ]
            result.permissions = permissions
            results.append(result)

        return response_from(
            schemas.EndpointListResponse(
                result=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def assign_permission(self, request: Request, body: schemas.AssignEndpointPermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.endpoint_service.add_permission(
                EndpointPermissionBinding(
                    endpoint=EndpointReference(endpoint_id=body.id, endpoint_path=body.endpoint),
                    permission=PermissionReference(
                        permission_id=body.permission.id,
                        permission_title=body.permission.permission_title,
                    ),
                ),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationAlreadyExistsError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.AssignEndpointPermissionResponse(), status=201)

    async def remove_permission(self, request: Request, body: schemas.RemoveEndpointPermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.endpoint_service.remove_permission(
                EndpointPermissionBinding(
                    endpoint=EndpointReference(endpoint_id=body.id, endpoint_path=body.endpoint),
                    permission=PermissionReference(
                        permission_id=body.permission.id,
                        permission_title=body.permission.permission_title,
                    ),
                ),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationNotFoundError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.RemoveEndpointPermissionResponse(), status=204)


def register_routes(admin_blueprint, identity_access):
    controller = EndpointAdminController(endpoint_service=identity_access.endpoint_admin_service)

    add_route(
        admin_blueprint,
        "/endpoints",
        methods=["GET"],
        handler=controller.list_endpoints,
        query=schemas.EndpointListQuery,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/endpoints/permissions",
        methods=["POST"],
        handler=controller.assign_permission,
        json=schemas.AssignEndpointPermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/endpoints/permissions",
        methods=["DELETE"],
        handler=controller.remove_permission,
        json=schemas.RemoveEndpointPermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
