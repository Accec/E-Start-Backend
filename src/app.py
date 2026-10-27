import logging
import os

from sanic import Blueprint, Sanic
from sanic.request import Request
from sanic_ext.exceptions import ValidationError

from core.config import Config
from core.constants import SERVER_LOGGER
from core.http import http_response
from core.responses import InvalidArgumentsError
from domains.audit.controller.router import register_routes as register_audit_routes
from domains.audit.repositories.logs import AuditLogRepository
from domains.audit.services.logs import AuditLogService
from domains.identity_access.cache import RedisAuthorizationCache
from domains.identity_access.controller.router import register_routes as register_identity_access_routes
from domains.identity_access.repositories.endpoints import EndpointRepository
from domains.identity_access.repositories.permissions import PermissionRepository
from domains.identity_access.repositories.roles import RoleRepository
from domains.identity_access.repositories.users import UserRepository
from domains.identity_access.security import JwtTokenIssuer, PasswordCredentialService
from domains.identity_access.services.auth import AuthService
from domains.identity_access.services.authorization import AuthorizationService
from domains.identity_access.services.dashboard import DashboardService
from domains.identity_access.services.endpoints import EndpointAdminService
from domains.identity_access.services.permissions import PermissionAdminService
from domains.identity_access.services.roles import RoleAdminService
from domains.identity_access.services.users import UserAdminService
from domains.operations.controller.router import register_routes as register_operations_routes
from domains.operations.scheduler_gateway import SchedulerGateway
from domains.operations.services.jobs import SchedulerJobService
from infra.database import register_database
from infra.logging import setup_application_loggers
from infra.redis import RedisClient
from infra.scheduler import Scheduler
from infra.security.jwt import JwtAuth
from infra.web.health import register_health_routes
from middleware.request_handling.request_handling import request_handling


def create_app(config: Config, redis_client: RedisClient, scheduler: Scheduler) -> Sanic:
    # Sanic's built-in logging bootstrap installs its own handlers and format,
    # which causes duplicate output once the application mounts its own logger.
    server = Sanic(config.app, configure_logging=False)
    config.apply_runtime_paths(os.getcwd())
    os.environ["LOG_PATH"] = config.logs_path
    setup_application_loggers()

    server.config.SERVER_NAME = f"{config.sanic_host}:{config.sanic_port}"
    server.config.FORWARDED_SECRET = config.forwarded_secret
    server.config.CORS_ORIGINS = ";".join(config.cors_domains)
    server.ext.openapi.add_security_scheme("token", "http", scheme="bearer", bearer_format="JWT")
    register_database(server, config)
    server.middleware(request_handling)

    audit_service = AuditLogService(logs=AuditLogRepository())
    credentials = PasswordCredentialService()
    users = UserRepository()
    roles = RoleRepository()
    permissions = PermissionRepository()
    endpoints = EndpointRepository()
    authorization_service = AuthorizationService(
        users=users,
        endpoints=endpoints,
        audit_logger=audit_service,
        cache=RedisAuthorizationCache(redis_client),
    )
    jwt_auth = JwtAuth(secret_key=config.jwt_secret_key, authorization_service=authorization_service)
    auth_service = AuthService(
        users=users,
        roles=roles,
        audit_logger=audit_service,
        credentials=credentials,
        token_issuer=JwtTokenIssuer(config.jwt_secret_key),
        token_ttl_seconds=config.jwt_exp_time,
    )
    user_service = UserAdminService(
        users=users, roles=roles, audit_logger=audit_service, credentials=credentials,
    )
    role_service = RoleAdminService(roles=roles, permissions=permissions, audit_logger=audit_service)
    permission_service = PermissionAdminService(permissions=permissions, audit_logger=audit_service)
    endpoint_service = EndpointAdminService(
        endpoints=endpoints, permissions=permissions, audit_logger=audit_service,
    )
    job_service = SchedulerJobService(jobs=SchedulerGateway(scheduler=scheduler))

    user_blueprint = Blueprint(name="user", url_prefix="/user", version=1, version_prefix="/api/v")
    admin_blueprint = Blueprint(name="admin", url_prefix="/admin", version=1, version_prefix="/api/v")
    system_blueprint = Blueprint(name="system", url_prefix="/system", version=1, version_prefix="/api/v")

    @user_blueprint.exception(ValidationError)
    async def user_validation_error(request: Request, exception: ValidationError):
        return http_response(InvalidArgumentsError.code, InvalidArgumentsError.msg, exception.message, status=400)

    @admin_blueprint.exception(ValidationError)
    async def admin_validation_error(request: Request, exception: ValidationError):
        return http_response(InvalidArgumentsError.code, InvalidArgumentsError.msg, exception.message, status=400)

    register_identity_access_routes(
        admin_blueprint,
        user_blueprint,
        auth_service=auth_service,
        dashboard_service=DashboardService(users=users),
        user_service=user_service,
        role_service=role_service,
        permission_service=permission_service,
        endpoint_service=endpoint_service,
        jwt_auth=jwt_auth,
    )
    register_audit_routes(admin_blueprint, audit_service=audit_service, jwt_auth=jwt_auth)
    register_operations_routes(admin_blueprint, job_service=job_service, jwt_auth=jwt_auth)
    register_health_routes(system_blueprint, app_name=config.app, redis_client=redis_client)

    logger = logging.getLogger(SERVER_LOGGER)
    for blueprint in (user_blueprint, admin_blueprint, system_blueprint):
        logger.info("[Blueprint] - [%s] is loaded", blueprint.name)
        server.blueprint(blueprint)
    return server


def create_http_app(config: Config) -> Sanic:
    redis_client = RedisClient(config.redis_url)
    return create_app(config, redis_client, Scheduler(redis_client))
