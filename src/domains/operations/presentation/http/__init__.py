from .admin import register_routes as register_admin_routes


def register_routes(admin_blueprint, operations_bootstrap, jwt_auth):
    register_admin_routes(admin_blueprint, operations_bootstrap, jwt_auth)
