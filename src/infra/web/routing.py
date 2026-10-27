from sanic_ext import validate

from infra.security.rate_limit import rate_limit


def build_route_name(handler) -> str:
    qualname = getattr(handler, "__qualname__", getattr(handler, "__name__", "handler"))
    return qualname.replace(".", "_")


def build_route_handler(handler, *, query=None, json=None, authorize=False, jwt_auth=None, limit=None):
    wrapped = handler

    if authorize:
        if jwt_auth is None:
            raise ValueError("jwt_auth is required when authorize=True")
        wrapped = jwt_auth.permissions_authorized()(wrapped)
    if query is not None:
        wrapped = validate(query=query)(wrapped)
    if json is not None:
        wrapped = validate(json=json)(wrapped)
    if limit is not None:
        wrapped = rate_limit(*limit)(wrapped)

    return wrapped


def add_route(blueprint, uri: str, *, methods: list[str], handler, query=None, json=None, authorize=False, jwt_auth=None, limit=None, name: str | None = None):
    blueprint.add_route(
        build_route_handler(
            handler,
            query=query,
            json=json,
            authorize=authorize,
            jwt_auth=jwt_auth,
            limit=limit,
        ),
        uri,
        methods=methods,
        name=name or build_route_name(handler),
    )
