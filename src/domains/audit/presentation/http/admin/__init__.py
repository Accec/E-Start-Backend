from .logs import register_routes as register_log_routes


def register_routes(admin_blueprint, audit_bootstrap, jwt_auth):
    register_log_routes(admin_blueprint, audit_bootstrap, jwt_auth)


__all__ = ["register_routes"]
