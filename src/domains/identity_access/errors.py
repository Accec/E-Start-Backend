class IdentityAccessError(Exception):
    pass


class ResourceNotFoundError(IdentityAccessError):
    pass


class DuplicateResourceError(IdentityAccessError):
    pass


class RelationAlreadyExistsError(IdentityAccessError):
    pass


class RelationNotFoundError(IdentityAccessError):
    pass


class AuthenticationFailedError(IdentityAccessError):
    pass


class UserInactiveError(AuthenticationFailedError):
    pass
