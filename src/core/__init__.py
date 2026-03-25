__all__ = ["Config"]


def __getattr__(name):
    if name == "Config":
        from .config import Config

        return Config
    raise AttributeError(f"module 'core' has no attribute {name!r}")
