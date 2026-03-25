from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from ....application.contracts import (
    CreateRoleCommand,
    RolePermissionBinding,
    UpdateRoleCommand,
)
from ....domain import PermissionReference, RoleListQuery, RoleReference
from domains.identity_access.domain.errors import (
    DuplicateResourceError,
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
)

from ...schemas.admin import roles as schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    response_from,
    schema_from,
)


@dataclass(slots=True)
class RoleAdminController:
    role_service: object

    async def list_roles(self, request: Request, query: schemas.RoleListQuery):
        role_query = RoleListQuery(role_id=query.id, role_name=query.role_name, page=query.page, page_size=query.page_size)
        page_result = await self.role_service.list_roles(role_query)

        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.RoleSummary)
            permissions = [
                schema_from(permission, schemas.PermissionSummary) for permission in await item.permissions.all()
            ]
            result.permissions = permissions
            results.append(result)

        return response_from(
            schemas.RoleListResponse(
                result=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def create_role(self, request: Request, body: schemas.CreateRoleBody):
        try:
            await self.role_service.create_role(
                CreateRoleCommand(role_name=body.role_name),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.CreateRoleResponse(), status=201)

    async def delete_role(self, request: Request, body: schemas.DeleteRoleBody):
        try:
            await self.role_service.delete_role(
                RoleReference(role_id=body.id, role_name=body.role_name),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.DeleteRoleResponse(), status=204)

    async def update_role(self, request: Request, body: schemas.UpdateRoleBody):
        try:
            await self.role_service.update_role(
                UpdateRoleCommand(role_id=body.id, role_name=body.role_name),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.UpdateRoleResponse(), status=201)

    async def assign_permission(self, request: Request, body: schemas.AssignRolePermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.role_service.add_permission(
                RolePermissionBinding(
                    role=RoleReference(role_id=body.id, role_name=body.role_name),
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

        return response_from(schemas.AssignRolePermissionResponse(), status=201)

    async def remove_permission(self, request: Request, body: schemas.RemoveRolePermissionBody):
        if body.permission is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.role_service.remove_permission(
                RolePermissionBinding(
                    role=RoleReference(role_id=body.id, role_name=body.role_name),
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

        return response_from(schemas.RemoveRolePermissionResponse(), status=204)


def register_routes(admin_blueprint, identity_access):
    controller = RoleAdminController(role_service=identity_access.role_admin_service)

    add_route(
        admin_blueprint,
        "/roles",
        methods=["GET"],
        handler=controller.list_roles,
        query=schemas.RoleListQuery,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["POST"],
        handler=controller.create_role,
        json=schemas.CreateRoleBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["DELETE"],
        handler=controller.delete_role,
        json=schemas.DeleteRoleBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles",
        methods=["PUT"],
        handler=controller.update_role,
        json=schemas.UpdateRoleBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles/permissions",
        methods=["POST"],
        handler=controller.assign_permission,
        json=schemas.AssignRolePermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/roles/permissions",
        methods=["DELETE"],
        handler=controller.remove_permission,
        json=schemas.RemoveRolePermissionBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
