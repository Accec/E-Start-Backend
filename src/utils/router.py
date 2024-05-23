from sanic import Blueprint
from utils.create_app import autodiscover_api, autodiscover_exceptions


Blueprints = []

def register_blueprint(bp):
    Blueprints.append(bp)
    return bp

UserBlueprint = register_blueprint(Blueprint(name="user", url_prefix="/user", version=1, version_prefix="/api/v"))
AdminBlueprint = register_blueprint(Blueprint(name="admin", url_prefix="/admin", version=1, version_prefix="/api/v"))

autodiscover_api()
autodiscover_exceptions()
