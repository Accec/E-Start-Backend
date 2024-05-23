from utils.router import AdminBlueprint

from sanic.request import Request
from sanic_ext.exceptions import ValidationError


from utils.response import ArgsInvalidError
from utils.util import http_response

@AdminBlueprint.exception(ValidationError)
async def validation_error(request: Request, exception: ValidationError):
    return http_response(ArgsInvalidError.code, ArgsInvalidError.msg, exception.message, status=500)



