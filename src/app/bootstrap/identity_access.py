from dataclasses import dataclass

from app.bootstrap.audit import AuditBootstrap
from core.config import Config
from infra.redis import RedisClient
from infra.security.jwt import JwtAuth

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
from domains.identity_access.infrastructure import (
    JwtTokenIssuer,
    PasswordCredentialService,
    RedisAuthorizationCache,
)
from domains.identity_access.infrastructure.repos import EndpointRepository, PermissionRepository, RoleRepository, UserRepository


@dataclass(slots=True)
class IdentityAccessBootstrap:
    config: Config
    audit: AuditBootstrap
    credentials: PasswordCredentialService
    redis_client: RedisClient
    authorization_cache: RedisAuthorizationCache
    user_repository: UserRepository
    role_repository: RoleRepository
    permission_repository: PermissionRepository
    endpoint_repository: EndpointRepository
    authorization_service: AuthorizationService
    token_issuer: JwtTokenIssuer
    auth_service: AuthService
    dashboard_service: DashboardService
    user_admin_service: UserAdminService
    role_admin_service: RoleAdminService
    permission_admin_service: PermissionAdminService
    endpoint_admin_service: EndpointAdminService
    bootstrap_service: BootstrapService
    jwt_auth: JwtAuth


__all__ = ["IdentityAccessBootstrap"]
