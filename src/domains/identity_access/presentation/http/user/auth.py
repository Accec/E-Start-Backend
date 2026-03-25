import logging
from dataclasses import dataclass

from sanic.request import Request

from app.bootstrap.routing import add_route
from core.constants import API_LOGGER
from core.responses import InvalidArgumentsError, InvalidCredentialsError, UserAlreadyExistsError
from domains.identity_access.domain.errors import (
    AuthenticationFailedError,
    DuplicateResourceError,
    ResourceNotFoundError,
    UserInactiveError,
)

from ...schemas.user import auth as schemas
from ..support import invalid_arguments_response, request_meta_from, response_from


logger = logging.getLogger(API_LOGGER)


@dataclass(slots=True)
class UserAuthController:
    auth_service: object

    async def login(self, request: Request, body: schemas.LoginBody):
        try:
            token = await self.auth_service.login(body.account, body.password, request_meta_from(request))
        except (AuthenticationFailedError, UserInactiveError):
            return response_from(
                schemas.InvalidCredentialsResponse(
                    code=InvalidCredentialsError.code,
                    msg=InvalidCredentialsError.msg,
                ),
                status=401,
            )

        return response_from(schemas.LoginResponse(token=token), status=200)

    async def register(self, request: Request, body: schemas.RegisterBody):
        try:
            await self.auth_service.register(body.account, body.password, request_meta_from(request))
        except DuplicateResourceError:
            return response_from(
                schemas.AccountAlreadyExistsResponse(
                    code=UserAlreadyExistsError.code,
                    msg=UserAlreadyExistsError.msg,
                ),
                status=400,
            )
        except ResourceNotFoundError:
            return invalid_arguments_response(schemas.ArgsInvalidResponse)

        logger.info(f"[User] - [{body.account}] Register")
        return response_from(schemas.RegisterResponse(), status=201)


def register_routes(user_blueprint, identity_access):
    controller = UserAuthController(auth_service=identity_access.auth_service)

    add_route(
        user_blueprint,
        "/login",
        methods=["POST"],
        handler=controller.login,
        json=schemas.LoginBody,
        limit=(5, 60),
    )
    add_route(
        user_blueprint,
        "/register",
        methods=["POST"],
        handler=controller.register,
        json=schemas.RegisterBody,
        limit=(5, 60),
    )
