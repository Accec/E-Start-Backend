from importlib import import_module


__all__ = [
    "ApplicationBootstrap",
    "ApplicationRuntime",
    "build_bootstrap",
    "build_runtime",
    "create_app",
    "get_blueprints",
    "setup_application_loggers",
    "start_http_server",
    "start_scheduler",
]


_EXPORT_MAP = {
    "ApplicationBootstrap": (".container", "ApplicationBootstrap"),
    "build_bootstrap": (".container", "build_bootstrap"),
    "create_app": (".application", "create_app"),
    "setup_application_loggers": (".logging", "setup_application_loggers"),
    "get_blueprints": (".routes", "get_blueprints"),
    "ApplicationRuntime": (".runtime", "ApplicationRuntime"),
    "build_runtime": (".runtime", "build_runtime"),
    "start_http_server": (".runtime", "start_http_server"),
    "start_scheduler": (".runtime", "start_scheduler"),
}


def __getattr__(name: str):
    try:
        module_name, attr_name = _EXPORT_MAP[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    return getattr(import_module(module_name, __name__), attr_name)
