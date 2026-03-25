from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from ....application.contracts import CreateUserCommand, UpdateUserCommand, UserRoleBinding
from ....domain import RoleReference, UserListQuery, UserReference
from domains.identity_access.domain.errors import (
    DuplicateResourceError,
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
)

from ...schemas.admin import users as schemas
from ..support import (
    actor_user_id_from,
    invalid_arguments_response,
    request_meta_from,
    response_from,
    schema_from,
    schema_list_from,
)


@dataclass(slots=True)
class UserAdminController:
    user_service: object

    async def list_users(self, request: Request, query: schemas.UserListQuery):
        user_query = UserListQuery(user_id=query.id, account=query.account, page=query.page, page_size=query.page_size)
        page_result = await self.user_service.list_users(user_query)

        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.UserSummary)
            roles = schema_list_from(await item.roles.all(), schemas.RoleSummary)
            result.roles = roles
            results.append(result)

        return response_from(
            schemas.UserListResponse(
                result=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def create_user(self, request: Request, body: schemas.CreateUserBody):
        try:
            await self.user_service.create_user(
                CreateUserCommand(account=body.account, password=body.password),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.CreateUserResponse(), status=201)

    async def update_user(self, request: Request, body: schemas.UpdateUserBody):
        try:
            await self.user_service.update_user(
                UpdateUserCommand(user_id=body.id, account=body.account, password=body.password),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.UpdateUserResponse(), status=201)

    async def assign_role(self, request: Request, body: schemas.AssignUserRoleBody):
        if body.role is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.user_service.assign_role(
                UserRoleBinding(
                    user=UserReference(user_id=body.id, account=body.account),
                    role=RoleReference(role_id=body.role.id, role_name=body.role.role_name),
                ),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationAlreadyExistsError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.AssignUserRoleResponse(), status=201)

    async def remove_role(self, request: Request, body: schemas.RemoveUserRoleBody):
        if body.role is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.user_service.remove_role(
                UserRoleBinding(
                    user=UserReference(user_id=body.id, account=body.account),
                    role=RoleReference(role_id=body.role.id, role_name=body.role.role_name),
                ),
                actor_user_id_from(request),
                request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationNotFoundError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return response_from(schemas.RemoveUserRoleResponse(), status=204)


def register_routes(admin_blueprint, identity_access):
    controller = UserAdminController(user_service=identity_access.user_admin_service)

    add_route(
        admin_blueprint,
        "/users",
        methods=["GET"],
        handler=controller.list_users,
        query=schemas.UserListQuery,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users",
        methods=["POST"],
        handler=controller.create_user,
        json=schemas.CreateUserBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users",
        methods=["PUT"],
        handler=controller.update_user,
        json=schemas.UpdateUserBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users/roles",
        methods=["POST"],
        handler=controller.assign_role,
        json=schemas.AssignUserRoleBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users/roles",
        methods=["DELETE"],
        handler=controller.remove_role,
        json=schemas.RemoveUserRoleBody,
        authorize=True,
        jwt_auth=identity_access.jwt_auth,
    )
