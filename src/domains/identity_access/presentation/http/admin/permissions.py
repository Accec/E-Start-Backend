from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from ....application.contracts import (
    CreatePermissionCommand,
    UpdatePermissionCommand,
)
from ....domain import PermissionListQuery, PermissionReference
from domains.identity_access.domain.errors import DuplicateResourceError, ResourceNotFoundError

from ...schemas.admin import permissions as schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    response_from,
    schema_list_from,
)


@dataclass(slots=True)
class PermissionAdminController:
    permission_service: object

    async def list_permissions(self, request: Request, query: schemas.PermissionListQuery):
        permission_query = PermissionListQuery(
            permission_id=query.id,
            permission_title=query.permission_title,
            page=query.page,
            page_size=query.page_size,
        )
        page_result = await self.permission_service.list_permissions(permission_query)

        results = schema_list_from(page_result.items, schemas.PermissionSummary)
        return response_from(
            schemas.PermissionListResponse(
                result=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def create_permission(self, request: Request, body: schemas.CreatePermissionBody):
        try:
            await self.permission_service.create_permission(
                CreatePermissionCommand(permission_title=body.permission_title),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.CreatePermissionResponse(), status=201)

    async def delete_permission(self, request: Request, body: schemas.DeletePermissionBody):
        try:
            await self.permission_service.delete_permission(
                PermissionReference(permission_id=body.id, permission_title=body.permission_title),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.DeletePermissionResponse(), status=204)

    async def update_permission(self, request: Request, body: schemas.UpdatePermissionBody):
        try:
            await self.permission_service.update_permission(
                UpdatePermissionCommand(permission_id=body.id, permission_title=body.permission_title),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.UpdatePermissionResponse(), status=201)


def register_routes(admin_blueprint, identity_access):
    controller = PermissionAdminController(permission_service=identity_access.permission_admin_service)

    add_route(
        admin_blueprint,
        "/permissions",
        methods=["GET"],
        handler=controller.list_permissions,
        query=schemas.PermissionListQuery,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["POST"],
        handler=controller.create_permission,
        json=schemas.CreatePermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["DELETE"],
        handler=controller.delete_permission,
        json=schemas.DeletePermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["PUT"],
        handler=controller.update_permission,
        json=schemas.UpdatePermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
