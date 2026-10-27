from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import PaginatedResponse, Response
from core.http import schema_response
from domains.identity_access.services.permissions import PermissionAdminService

from infra.web.routing import add_route
from domains.identity_access.errors import DuplicateResourceError, ResourceNotFoundError

from . import schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    schema_list_from,
)


@dataclass(slots=True)
class PermissionAdminController:
    permission_service: PermissionAdminService

    async def list_permissions(self, request: Request, query: schemas.GetPermissionQuery):
        page_result = await self.permission_service.list_permissions(
            permission_id=query.id,
            permission_title=query.permission_title,
            page=query.page,
            page_size=query.page_size,
        )
        results = schema_list_from(page_result.items, schemas.PermissionSummary)
        return schema_response(
            PaginatedResponse(
                results=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def create_permission(self, request: Request, body: schemas.PostPermissionBody):
        try:
            await self.permission_service.create_permission(
                permission_title=body.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def delete_permission(self, request: Request, body: schemas.DeletePermissionBody):
        try:
            await self.permission_service.delete_permission(
                permission_id=body.id,
                permission_title=body.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=204)

    async def update_permission(self, request: Request, body: schemas.PutPermissionBody):
        try:
            await self.permission_service.update_permission(
                permission_id=body.id,
                permission_title=body.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)


def register_routes(admin_blueprint, *, permission_service, jwt_auth):
    controller = PermissionAdminController(permission_service=permission_service)

    add_route(
        admin_blueprint,
        "/permissions",
        methods=["GET"],
        handler=controller.list_permissions,
        query=schemas.GetPermissionQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["POST"],
        handler=controller.create_permission,
        json=schemas.PostPermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["DELETE"],
        handler=controller.delete_permission,
        json=schemas.DeletePermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/permissions",
        methods=["PUT"],
        handler=controller.update_permission,
        json=schemas.PutPermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
