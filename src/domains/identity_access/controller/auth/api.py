import logging
from dataclasses import dataclass

from sanic.request import Request

from core.api_schema import Response
from core.http import schema_response
from domains.identity_access.services.auth import AuthService

from infra.web.routing import add_route
from core.constants import API_LOGGER
from core.responses import InvalidArgumentsError, InvalidCredentialsError, UserAlreadyExistsError
from domains.identity_access.errors import (
    AuthenticationFailedError,
    DuplicateResourceError,
    ResourceNotFoundError,
    UserInactiveError,
)

from . import schemas
from ..support import invalid_arguments_response, request_meta_from


logger = logging.getLogger(API_LOGGER)


@dataclass(slots=True)
class UserAuthController:
    auth_service: AuthService

    async def login(self, request: Request, body: schemas.PostLoginBody):
        try:
            token = await self.auth_service.login(
                account=body.account, password=body.password, request_meta=request_meta_from(request),
            )
        except (AuthenticationFailedError, UserInactiveError):
            return schema_response(
                schemas.InvalidCredentialsResponse(
                    code=InvalidCredentialsError.code,
                    msg=InvalidCredentialsError.msg,
                ),
                status=401,
            )

        return schema_response(Response(results=schemas.LoginPayload(token=token)), status=200)

    async def register(self, request: Request, body: schemas.PostRegisterBody):
        try:
            await self.auth_service.register(
                account=body.account, password=body.password, request_meta=request_meta_from(request),
            )
        except DuplicateResourceError:
            return schema_response(
                schemas.AccountAlreadyExistsResponse(
                    code=UserAlreadyExistsError.code,
                    msg=UserAlreadyExistsError.msg,
                ),
                status=400,
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        logger.info(f"[User] - [{body.account}] Register")
        return schema_response(Response(), status=201)


def register_routes(user_blueprint, *, auth_service):
    controller = UserAuthController(auth_service=auth_service)

    add_route(
        user_blueprint,
        "/login",
        methods=["POST"],
        handler=controller.login,
        json=schemas.PostLoginBody,
        limit=(5, 60),
    )
    add_route(
        user_blueprint,
        "/register",
        methods=["POST"],
        handler=controller.register,
        json=schemas.PostRegisterBody,
        limit=(5, 60),
    )
