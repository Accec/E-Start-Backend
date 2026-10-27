from .auth.api import register_routes as register_auth_routes
from .dashboard.api import register_routes as register_dashboard_routes
from .endpoints.api import register_routes as register_endpoint_routes
from .permissions.api import register_routes as register_permission_routes
from .roles.api import register_routes as register_role_routes
from .users.api import register_routes as register_user_routes


def register_routes(
    admin_blueprint,
    user_blueprint,
    *,
    auth_service,
    dashboard_service,
    user_service,
    role_service,
    permission_service,
    endpoint_service,
    jwt_auth,
):
    register_auth_routes(user_blueprint, auth_service=auth_service)
    register_dashboard_routes(user_blueprint, dashboard_service=dashboard_service, jwt_auth=jwt_auth)
    register_user_routes(admin_blueprint, user_service=user_service, jwt_auth=jwt_auth)
    register_role_routes(admin_blueprint, role_service=role_service, jwt_auth=jwt_auth)
    register_permission_routes(admin_blueprint, permission_service=permission_service, jwt_auth=jwt_auth)
    register_endpoint_routes(admin_blueprint, endpoint_service=endpoint_service, jwt_auth=jwt_auth)
