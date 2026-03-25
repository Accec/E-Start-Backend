from sanic import Blueprint
from sanic.request import Request
from sanic_ext.exceptions import ValidationError

from app.bootstrap.container import ApplicationBootstrap
from core.http import http_response
from core.responses import InvalidArgumentsError
from domains.audit.presentation.http import register_routes as register_audit_routes
from domains.identity_access.presentation.http import register_routes as register_identity_access_routes
from domains.operations.presentation.http import register_routes as register_operations_routes
from infra.web.health import register_health_routes


def build_blueprints():
    user_blueprint = Blueprint(name="user", url_prefix="/user", version=1, version_prefix="/api/v")
    admin_blueprint = Blueprint(name="admin", url_prefix="/admin", version=1, version_prefix="/api/v")
    system_blueprint = Blueprint(name="system", url_prefix="/system", version=1, version_prefix="/api/v")

    @user_blueprint.exception(ValidationError)
    async def user_validation_error(request: Request, exception: ValidationError):
        return http_response(InvalidArgumentsError.code, InvalidArgumentsError.msg, exception.message, status=400)

    @admin_blueprint.exception(ValidationError)
    async def admin_validation_error(request: Request, exception: ValidationError):
        return http_response(InvalidArgumentsError.code, InvalidArgumentsError.msg, exception.message, status=400)

    return user_blueprint, admin_blueprint, system_blueprint


def register_routes(*, admin_blueprint, user_blueprint, system_blueprint, bootstrap: ApplicationBootstrap):
    identity_access = bootstrap.identity_access
    register_identity_access_routes(admin_blueprint, user_blueprint, identity_access)
    register_audit_routes(admin_blueprint, bootstrap.audit, identity_access.jwt_auth)
    register_operations_routes(admin_blueprint, bootstrap.operations, identity_access.jwt_auth)
    register_health_routes(system_blueprint, bootstrap)


def get_blueprints(bootstrap: ApplicationBootstrap):
    user_blueprint, admin_blueprint, system_blueprint = build_blueprints()
    register_routes(
        admin_blueprint=admin_blueprint,
        user_blueprint=user_blueprint,
        system_blueprint=system_blueprint,
        bootstrap=bootstrap,
    )
    return [user_blueprint, admin_blueprint, system_blueprint]
