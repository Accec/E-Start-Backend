from .admin import register_routes as register_admin_routes
from .user import register_routes as register_user_routes


def register_routes(admin_blueprint, user_blueprint, identity_access):
    register_user_routes(user_blueprint, identity_access)
    register_admin_routes(admin_blueprint, identity_access)
