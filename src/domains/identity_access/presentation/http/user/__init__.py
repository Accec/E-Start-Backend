from .auth import register_routes as register_auth_routes
from .dashboard import register_routes as register_dashboard_routes


def register_routes(user_blueprint, identity_access):
    register_auth_routes(user_blueprint, identity_access)
    register_dashboard_routes(user_blueprint, identity_access)


__all__ = ["register_routes"]
