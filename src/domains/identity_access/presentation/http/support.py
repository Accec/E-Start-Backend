from typing import Any, Iterable, TypeVar

from pydantic import BaseModel
from sanic.request import Request

from core.http import schema_response
from core.responses import InvalidArgumentsError
from domains.identity_access.domain.request_meta import RequestMeta


SchemaModel = TypeVar("SchemaModel", bound=BaseModel)


def request_meta_from(request: Request) -> RequestMeta:
    return RequestMeta(
        api=request.ctx.request_path,
        ip=request.ctx.real_ip,
        ua=request.ctx.ua,
    )


def actor_user_id_from(request: Request) -> int:
    return int(request.ctx.user["user_id"])


def schema_from(source: Any, schema_model: type[SchemaModel]) -> SchemaModel:
    return schema_model.model_validate(source, from_attributes=True)


def schema_list_from(items: Iterable[Any], schema_model: type[SchemaModel]) -> list[SchemaModel]:
    return [schema_from(item, schema_model) for item in items]


def response_from(schema: BaseModel, *, status=200):
    return schema_response(schema, status=status)


def invalid_arguments_response(response_model: type[BaseModel]):
    return response_from(response_model(code=InvalidArgumentsError.code, msg=InvalidArgumentsError.msg), status=400)
