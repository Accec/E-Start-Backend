from core.constants import UserStatus

from .errors import (
    AuthenticationFailedError,
    DuplicateResourceError,
    RelationAlreadyExistsError,
    RelationNotFoundError,
    ResourceNotFoundError,
    UserInactiveError,
)


def ensure_exists(resource, message: str):
    if not resource:
        raise ResourceNotFoundError(message)


def ensure_not_exists(exists: bool, message: str):
    if exists:
        raise DuplicateResourceError(message)


def ensure_relation_absent(exists: bool, message: str):
    if exists:
        raise RelationAlreadyExistsError(message)


def ensure_relation_present(exists: bool, message: str):
    if not exists:
        raise RelationNotFoundError(message)


def validate_login_candidate(user, password_is_valid: bool):
    if not user or not password_is_valid:
        raise AuthenticationFailedError("account or password invalid")

    if user.status == UserStatus.INACTIVE:
        raise UserInactiveError("user is inactive")
