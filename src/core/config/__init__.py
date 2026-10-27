import logging
import os
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path
from typing import Any, ClassVar, get_args, get_origin

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    import yaml
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "PyYAML is required for YAML-based config loading. "
        "Install dependencies with `pip install -r src/requirements.txt`."
    ) from exc


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


_CONFIG_SECTIONS = {
    "app": {"name": "app", "debug": "debug", "timezone": "timezone"},
    "server": {
        "host": "sanic_host",
        "port": "sanic_port",
        "workers": "sanic_workers",
        "forwarded_secret": "forwarded_secret",
        "cors_domains": "cors_domains",
    },
    "paths": {
        "relative": "relative_path",
        "uploads": "uploads_path",
        "logs": "logs_path",
        "migrations": "migrations_path",
    },
    "jwt": {"secret_key": "jwt_secret_key", "exp_time": "jwt_exp_time"},
    "mysql": {
        "host": "mysql_host",
        "port": "mysql_port",
        "username": "mysql_username",
        "password": "mysql_password",
        "database": "mysql_database_name",
    },
    "redis": {"url": "redis_url"},
    "tools": {"pip": "pip"},
}


@dataclass(slots=True)
class ConfigModel:
    app: str = "Demo"
    debug: bool = True
    pip: str = "pip"
    relative_path: bool = True
    uploads_path: str = "uploads"
    logs_path: str = "logs"
    jwt_secret_key: str = ""
    sanic_host: str = "localhost"
    sanic_port: int = 8000
    sanic_workers: int = 1
    forwarded_secret: str = ""
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_username: str = "root"
    mysql_password: str = ""
    mysql_database_name: str = "demo"
    redis_url: str = "redis://127.0.0.1/0"
    cors_domains: list[str] = field(default_factory=lambda: ["localhost.com"])
    timezone: str = "UTC"
    jwt_exp_time: int = 86400
    migrations_path: str = "migrations"

    def apply_runtime_paths(self, cwd: str):
        if not self.relative_path:
            return
        root = Path(cwd)
        self.uploads_path = self._resolve_runtime_path(root, self.uploads_path)
        self.logs_path = self._resolve_runtime_path(root, self.logs_path)

    @staticmethod
    def _resolve_runtime_path(root: Path, raw_path: str) -> str:
        path = Path(raw_path)
        if path.is_absolute():
            return path.as_posix()
        return (root / path).resolve().as_posix()


class Config(ConfigModel):
    _config_dir: ClassVar[Path] = Path(__file__).resolve().parent

    @classmethod
    def _read_yaml(cls, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            content = yaml.safe_load(file) or {}
        if not isinstance(content, dict):
            raise TypeError(f"Config file [{path}] must contain a YAML mapping at the top level")
        return content

    @classmethod
    def _merge_dicts(cls, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = cls._merge_dicts(merged[key], value)
                continue
            merged[key] = value
        return merged

    @classmethod
    def _load_config(cls) -> tuple[dict[str, Any], str]:
        mode = os.environ.get("MODE", "sample").lower()
        base_config = cls._read_yaml(cls._config_dir / "base.yaml")
        mode_config_path = cls._config_dir / f"{mode}.yaml"

        if mode_config_path.exists():
            mode_config = cls._read_yaml(mode_config_path)
            config_name = mode
        else:
            logging.warning("[Config] - [%s] cannot be loaded, falling back to [sample]", mode)
            mode_config = cls._read_yaml(cls._config_dir / "sample.yaml")
            config_name = "sample"

        return cls._merge_dicts(base_config, mode_config), config_name

    @classmethod
    def _build_values(cls, raw_data: dict[str, Any]) -> dict[str, Any]:
        config_fields = {config_field.name: config_field for config_field in fields(ConfigModel)}
        unknown_sections = sorted(set(raw_data) - set(_CONFIG_SECTIONS))
        if unknown_sections:
            raise KeyError(f"Unknown config sections: {', '.join(unknown_sections)}")

        values = {}
        for section, keys in _CONFIG_SECTIONS.items():
            section_data = raw_data.get(section, {})
            if not isinstance(section_data, dict):
                raise TypeError(f"Config section [{section}] must contain a YAML mapping")
            unknown_keys = sorted(set(section_data) - set(keys))
            if unknown_keys:
                paths = ", ".join(f"{section}.{key}" for key in unknown_keys)
                raise KeyError(f"Unknown config keys: {paths}")

            for key, name in keys.items():
                config_field = config_fields[name]
                path = f"{section}.{key}"
                if key in section_data:
                    value = section_data[key]
                elif config_field.default is not MISSING:
                    value = config_field.default
                elif config_field.default_factory is not MISSING:
                    value = config_field.default_factory()
                else:
                    raise KeyError(f"Missing required config key: {path}")

                cls._validate_type(path, value, config_field.type)
                if name == "sanic_workers" and value < 1:
                    raise ValueError(f"Config key [{path}] must be greater than or equal to 1")
                values[name] = value

        return values

    @classmethod
    def _validate_type(cls, name: str, value: Any, expected_type):
        origin = get_origin(expected_type)
        if origin is list:
            item_type = get_args(expected_type)[0]
            if not isinstance(value, list) or any(not isinstance(item, item_type) for item in value):
                raise TypeError(f"Config key [{name}] must be a list[{item_type.__name__}]")
            return

        if expected_type is int and isinstance(value, bool):
            raise TypeError(f"Config key [{name}] must be an int")

        if not isinstance(value, expected_type):
            raise TypeError(f"Config key [{name}] must be a {expected_type.__name__}")

    @classmethod
    def load(cls) -> "Config":
        merged_config, config_name = cls._load_config()
        instance = cls(**cls._build_values(merged_config))
        logging.info("[Config] - [%s] is loaded", config_name)
        return instance


def load_config() -> Config:
    return Config.load()


__all__ = ["Config", "ConfigModel", "load_config"]
