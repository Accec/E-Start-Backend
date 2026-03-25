from .endpoints import register_routes as register_endpoint_routes
from .permissions import register_routes as register_permission_routes
from .roles import register_routes as register_role_routes
from .users import register_routes as register_user_routes


def register_routes(admin_blueprint, identity_access):
    register_user_routes(admin_blueprint, identity_access)
    register_role_routes(admin_blueprint, identity_access)
    register_permission_routes(admin_blueprint, identity_access)
    register_endpoint_routes(admin_blueprint, identity_access)


__all__ = ["register_routes"]
