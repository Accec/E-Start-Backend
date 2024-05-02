from sanic import Blueprint

UserBlueprint = Blueprint(name="user", url_prefix="user", version=1, version_prefix="/api/v")

from application.api.v1.user.register import api
from application.api.v1.user.login import api
from application.api.v1.user.dashboard import api

