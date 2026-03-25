from dataclasses import dataclass

from core.config import Config, load_config
from infra.redis import RedisClient
from infra.scheduler import Scheduler
from infra.security.jwt import JwtAuth

from domains.audit.application import AuditLogService
from domains.audit.infrastructure.repositories import AuditLogRepository
from domains.identity_access.application import AuthorizationService
from domains.identity_access.application.use_cases import (
    AuthService,
    BootstrapService,
    DashboardService,
    EndpointAdminService,
    PermissionAdminService,
    RoleAdminService,
    UserAdminService,
)
from domains.identity_access.infrastructure import JwtTokenIssuer, PasswordCredentialService, RedisAuthorizationCache
from domains.identity_access.infrastructure.repos import EndpointRepository, PermissionRepository, RoleRepository, UserRepository
from domains.operations.application import SchedulerJobService
from domains.operations.infrastructure.scheduler_gateway import SchedulerGateway
from .audit import AuditBootstrap
from .identity_access import IdentityAccessBootstrap
from .operations import OperationsBootstrap


@dataclass(slots=True)
class ApplicationBootstrap:
    config: Config
    audit: AuditBootstrap
    operations: OperationsBootstrap
    identity_access: IdentityAccessBootstrap


def build_bootstrap(config: Config | None = None):
    app_config = config or load_config()
    redis_client = RedisClient(app_config.redis_url)

    audit_log_repository = AuditLogRepository()
    audit_log_service = AuditLogService(logs=audit_log_repository)
    audit = AuditBootstrap(
        audit_log_repository=audit_log_repository,
        audit_log_service=audit_log_service,
    )

    scheduler = Scheduler(redis_client)
    scheduler_gateway = SchedulerGateway(scheduler=scheduler)
    scheduler_job_service = SchedulerJobService(jobs=scheduler_gateway)
    operations = OperationsBootstrap(
        scheduler=scheduler,
        scheduler_gateway=scheduler_gateway,
        scheduler_job_service=scheduler_job_service,
    )

    credentials = PasswordCredentialService()
    authorization_cache = RedisAuthorizationCache(redis_client)
    user_repository = UserRepository()
    role_repository = RoleRepository()
    permission_repository = PermissionRepository()
    endpoint_repository = EndpointRepository()
    authorization_service = AuthorizationService(
        users=user_repository,
        endpoints=endpoint_repository,
        audit_logger=audit.audit_log_service,
        cache=authorization_cache,
    )
    token_issuer = JwtTokenIssuer(app_config.jwt_secret_key)
    auth_service = AuthService(
        users=user_repository,
        roles=role_repository,
        audit_logger=audit.audit_log_service,
        credentials=credentials,
        token_issuer=token_issuer,
        token_ttl_seconds=app_config.jwt_exp_time,
    )
    dashboard_service = DashboardService(users=user_repository)
    user_admin_service = UserAdminService(
        users=user_repository,
        roles=role_repository,
        audit_logger=audit.audit_log_service,
        credentials=credentials,
    )
    role_admin_service = RoleAdminService(
        roles=role_repository,
        permissions=permission_repository,
        audit_logger=audit.audit_log_service,
    )
    permission_admin_service = PermissionAdminService(
        permissions=permission_repository,
        audit_logger=audit.audit_log_service,
    )
    endpoint_admin_service = EndpointAdminService(
        endpoints=endpoint_repository,
        permissions=permission_repository,
        audit_logger=audit.audit_log_service,
    )
    bootstrap_service = BootstrapService(
        users=user_repository,
        roles=role_repository,
        credentials=credentials,
    )
    jwt_auth = JwtAuth(
        secret_key=app_config.jwt_secret_key,
        authorization_service=authorization_service,
    )
    identity_access = IdentityAccessBootstrap(
        config=app_config,
        audit=audit,
        credentials=credentials,
        redis_client=redis_client,
        authorization_cache=authorization_cache,
        user_repository=user_repository,
        role_repository=role_repository,
        permission_repository=permission_repository,
        endpoint_repository=endpoint_repository,
        authorization_service=authorization_service,
        token_issuer=token_issuer,
        auth_service=auth_service,
        dashboard_service=dashboard_service,
        user_admin_service=user_admin_service,
        role_admin_service=role_admin_service,
        permission_admin_service=permission_admin_service,
        endpoint_admin_service=endpoint_admin_service,
        bootstrap_service=bootstrap_service,
        jwt_auth=jwt_auth,
    )

    return ApplicationBootstrap(
        config=app_config,
        audit=audit,
        operations=operations,
        identity_access=identity_access,
    )


__all__ = ["ApplicationBootstrap", "build_bootstrap"]
