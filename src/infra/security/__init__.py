from importlib import import_module


__all__ = ["JwtAuth", "generate_openid", "hash_password", "needs_rehash", "rate_limit", "verify_password"]


def __getattr__(name: str):
    if name == "JwtAuth":
        return getattr(import_module(".jwt", __name__), name)
    if name == "rate_limit":
        return getattr(import_module(".rate_limit", __name__), name)
    if name in {"generate_openid", "hash_password", "needs_rehash", "verify_password"}:
        return getattr(import_module(".passwords", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
