from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import PaginatedResponse, Response
from core.http import schema_response
from domains.identity_access.services.users import UserAdminService

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
    schema_list_from,
)


@dataclass(slots=True)
class UserAdminController:
    user_service: UserAdminService

    async def list_users(self, request: Request, query: schemas.GetUserQuery):
        page_result = await self.user_service.list_users(
            user_id=query.id, account=query.account, page=query.page, page_size=query.page_size,
        )

        results = []
        for item in page_result.items:
            result = schema_from(item, schemas.UserSummary)
            roles = schema_list_from(await item.roles.all(), schemas.RoleSummary)
            result.roles = roles
            results.append(result)

        return schema_response(
            PaginatedResponse(
                results=results,
                total_items=page_result.total_items,
                total_pages=page_result.total_pages,
            ),
            status=200,
        )

    async def create_user(self, request: Request, body: schemas.PostUserBody):
        try:
            await self.user_service.create_user(
                account=body.account,
                password=body.password,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except DuplicateResourceError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def update_user(self, request: Request, body: schemas.PutUserBody):
        try:
            await self.user_service.update_user(
                user_id=body.id,
                account=body.account,
                password=body.password,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def assign_role(self, request: Request, body: schemas.PostUserRoleBody):
        if body.role is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.user_service.assign_role(
                user_id=body.id,
                account=body.account,
                role_id=body.role.id,
                role_name=body.role.role_name,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationAlreadyExistsError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=201)

    async def remove_role(self, request: Request, body: schemas.DeleteUserRoleBody):
        if body.role is None:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)
        try:
            await self.user_service.remove_role(
                user_id=body.id,
                account=body.account,
                role_id=body.role.id,
                role_name=body.role.role_name,
                actor_user_id=actor_user_id_from(request),
                request_meta=request_meta_from(request),
            )
        except (ResourceNotFoundError, RelationNotFoundError):
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        return schema_response(Response(), status=204)


def register_routes(admin_blueprint, *, user_service, jwt_auth):
    controller = UserAdminController(user_service=user_service)

    add_route(
        admin_blueprint,
        "/users",
        methods=["GET"],
        handler=controller.list_users,
        query=schemas.GetUserQuery,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users",
        methods=["POST"],
        handler=controller.create_user,
        json=schemas.PostUserBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users",
        methods=["PUT"],
        handler=controller.update_user,
        json=schemas.PutUserBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users/roles",
        methods=["POST"],
        handler=controller.assign_role,
        json=schemas.PostUserRoleBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
    add_route(
        admin_blueprint,
        "/users/roles",
        methods=["DELETE"],
        handler=controller.remove_role,
        json=schemas.DeleteUserRoleBody,
        authorize=True,
        jwt_auth=jwt_auth,
    )
