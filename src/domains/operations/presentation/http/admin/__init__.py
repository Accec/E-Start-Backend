from .jobs import register_routes as register_job_routes


def register_routes(admin_blueprint, operations_bootstrap, jwt_auth):
    register_job_routes(admin_blueprint, operations_bootstrap, jwt_auth)


__all__ = ["register_routes"]
