from .logs.api import register_routes as register_log_routes


def register_routes(admin_blueprint, *, audit_service, jwt_auth):
    register_log_routes(admin_blueprint, audit_service=audit_service, jwt_auth=jwt_auth)
