from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import PaginatedResponse, Response
from core.http import schema_response
from domains.identity_access.services.roles import RoleAdminService

from infra.web.routing import add_route
from domains.identity_access.errors import (
    DuplicateResourceError,
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
)

from . import schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    schema_from,
)


@dataclass(slots=True)
class RoleAdminController:
    role_service: RoleAdminService

    async def list_roles(self, request: Request, query: schemas.GetRoleQuery):
        page_result = await self.role_service.list_roles(
            role_id=query.id, role_name=query.role_name, page=query.page, page_size=query.page_size,
        )

        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.RoleSummary)
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

    async def create_role(self, request: Request, body: schemas.PostRoleBody):
        try:
            await self.role_service.create_role(
                role_name=body.role_name,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def delete_role(self, request: Request, body: schemas.DeleteRoleBody):
        try:
            await self.role_service.delete_role(
                role_id=body.id,
                role_name=body.role_name,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=204)

    async def update_role(self, request: Request, body: schemas.PutRoleBody):
        try:
            await self.role_service.update_role(
                role_id=body.id,
                role_name=body.role_name,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def assign_permission(self, request: Request, body: schemas.PostRolePermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.role_service.add_permission(
                role_id=body.id,
                role_name=body.role_name,
                permission_id=body.permission.id,
                permission_title=body.permission.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationAlreadyExistsError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def remove_permission(self, request: Request, body: schemas.DeleteRolePermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.role_service.remove_permission(
                role_id=body.id,
                role_name=body.role_name,
                permission_id=body.permission.id,
                permission_title=body.permission.permission_title,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationNotFoundError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=204)


def register_routes(admin_blueprint, *, role_service, jwt_auth):
    controller = RoleAdminController(role_service=role_service)

    add_route(
        admin_blueprint,
        "/roles",
        methods=["GET"],
        handler=controller.list_roles,
        query=schemas.GetRoleQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["POST"],
        handler=controller.create_role,
        json=schemas.PostRoleBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["DELETE"],
        handler=controller.delete_role,
        json=schemas.DeleteRoleBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["PUT"],
        handler=controller.update_role,
        json=schemas.PutRoleBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles/permissions",
        methods=["POST"],
        handler=controller.assign_permission,
        json=schemas.PostRolePermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles/permissions",
        methods=["DELETE"],
        handler=controller.remove_permission,
        json=schemas.DeleteRolePermissionBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
