import json
import os
import re
import sys
import tempfile
import unittest
from dataclasses import asdict, fields
from pathlib import Path
from typing import get_origin
from unittest.mock import patch

import yaml


SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config import Config, ConfigModel


CONFIG_FIELDS = {
    "app": {"name": "app", "debug": "debug", "timezone": "timezone"},
    "server": {
        "host": "sanic_host", "port": "sanic_port", "workers": "sanic_workers",
        "forwarded_secret": "forwarded_secret", "cors_domains": "cors_domains",
    },
    "paths": {
        "relative": "relative_path", "uploads": "uploads_path", "logs": "logs_path",
        "migrations": "migrations_path",
    },
    "jwt": {"secret_key": "jwt_secret_key", "exp_time": "jwt_exp_time"},
    "mysql": {
        "host": "mysql_host", "port": "mysql_port", "username": "mysql_username",
        "password": "mysql_password", "database": "mysql_database_name",
    },
    "redis": {"url": "redis_url"},
    "tools": {"pip": "pip"},
}


def example_config():
    return {
        "app": {"name": "FixtureApp", "debug": False, "timezone": "Europe/Paris"},
        "server": {
            "host": "127.0.0.2", "port": 8123, "workers": 2,
            "forwarded_secret": "fixture-forwarded-secret", "cors_domains": ["fixture.invalid"],
        },
        "paths": {
            "relative": False, "uploads": "fixture-uploads", "logs": "fixture-logs",
            "migrations": "fixture-migrations",
        },
        "jwt": {"secret_key": "fixture-jwt-secret", "exp_time": 1234},
        "mysql": {
            "host": "fixture-db.invalid", "port": 3317, "username": "fixture-user",
            "password": "fixture-password", "database": "fixture_database",
        },
        "redis": {"url": "redis://fixture-cache.invalid:6381/7"},
        "tools": {"pip": "fixture-pip"},
    }


class ConfigurationTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config_dir = Path(directory.name)
        config_directory = patch.object(Config, "_config_dir", self.config_dir)
        config_directory.start()
        self.addCleanup(config_directory.stop)
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("MODE", None)

    def write_config(self, name, values):
        (self.config_dir / f"{name}.yaml").write_text(yaml.safe_dump(values), encoding="utf-8")

    def test_all_nested_fields_map_to_the_existing_runtime_attributes(self):
        raw = example_config()
        expected = {
            attribute: raw[group][name]
            for group, names in CONFIG_FIELDS.items()
            for name, attribute in names.items()
        }
        self.assertEqual(len(expected), 21)
        self.assertEqual(set(expected), {item.name for item in fields(ConfigModel)})
        self.assertEqual(Config._build_values(raw), expected)
        self.assertEqual(asdict(Config(**Config._build_values(raw))), expected)
        self.assertEqual(asdict(ConfigModel(**expected)), expected)
        self.assertEqual(asdict(Config(**expected)), expected)

    def test_missing_groups_and_fields_keep_runtime_defaults(self):
        defaults = asdict(ConfigModel())
        self.assertEqual(Config._build_values({}), defaults)
        self.assertEqual(Config._build_values({group: {} for group in CONFIG_FIELDS}), defaults)
        self.assertEqual(
            Config._build_values({"server": {"workers": 3}}),
            {**defaults, "sanic_workers": 3},
        )

    def test_default_lists_are_not_shared_between_configurations(self):
        first = Config._build_values({})
        second = Config._build_values({})
        first["cors_domains"].append("changed.invalid")
        self.assertEqual(second["cors_domains"], ConfigModel().cors_domains)

    def test_mode_defaults_to_sample_and_overrides_only_supplied_fields(self):
        self.write_config("base", {"app": {"name": "BaseFixture", "debug": False}, "server": {"port": 8123}})
        self.write_config("sample", {"app": {"name": "SampleFixture"}})
        config = Config.load()
        self.assertEqual(config.app, "SampleFixture")
        self.assertFalse(config.debug)
        self.assertEqual(config.sanic_port, 8123)
        self.assertEqual(config.sanic_workers, ConfigModel().sanic_workers)

    def test_mode_is_case_insensitive_and_nested_groups_merge(self):
        base = example_config()
        self.write_config("base", base)
        self.write_config("dev", {
            "server": {"port": 9001, "cors_domains": ["override.invalid"]},
            "mysql": {"username": "override-user"},
        })
        os.environ["MODE"] = "DeV"
        config = Config.load()
        expected = Config._build_values(base)
        expected.update(sanic_port=9001, cors_domains=["override.invalid"], mysql_username="override-user")
        self.assertEqual(asdict(config), expected)

    def test_missing_mode_falls_back_to_sample_with_base_values(self):
        self.write_config("base", {"server": {"port": 8123}})
        self.write_config("sample", {"app": {"name": "SampleFixture"}})
        os.environ["MODE"] = "MISSING"
        with self.assertLogs(level="WARNING") as logs:
            config = Config.load()
        self.assertEqual(config.app, "SampleFixture")
        self.assertEqual(config.sanic_port, 8123)
        self.assertTrue(any("missing" in message and "sample" in message for message in logs.output))

    def test_lists_replace_instead_of_append_including_empty_override(self):
        self.write_config("base", {"server": {"cors_domains": ["first.invalid", "second.invalid"]}})
        for override in (["override.invalid"], []):
            with self.subTest(override=override):
                self.write_config("sample", {"server": {"cors_domains": override}})
                self.assertEqual(Config.load().cors_domains, override)

    def test_validation_runs_after_base_and_mode_have_merged(self):
        self.write_config("base", {"server": {"port": "replaced-by-mode", "workers": 2}})
        self.write_config("sample", {"server": {"port": 8123}})
        config = Config.load()
        self.assertEqual(config.sanic_port, 8123)
        self.assertEqual(config.sanic_workers, 2)

    def test_unknown_groups_and_fields_report_the_nested_path(self):
        with self.assertRaisesRegex(KeyError, "unknown_group"):
            Config._build_values({"unknown_group": {}})
        for group in CONFIG_FIELDS:
            with self.subTest(group=group):
                with self.assertRaisesRegex(KeyError, re.escape(f"{group}.unknown_field")):
                    Config._build_values({group: {"unknown_field": "fixture"}})

    def test_old_flat_yaml_keys_are_rejected(self):
        for name, value in (("sanic_port", 8123), ("debug", False), ("jwt_secret_key", "fixture")):
            with self.subTest(name=name):
                with self.assertRaisesRegex(KeyError, name):
                    Config._build_values({name: value})
        with self.assertRaisesRegex(TypeError, "app"):
            Config._build_values({"app": "OldFlatApp"})

    def test_groups_must_be_mappings(self):
        for group in CONFIG_FIELDS:
            for value in (None, [], "fixture", False, 1):
                with self.subTest(group=group, value=value):
                    with self.assertRaisesRegex(TypeError, group):
                        Config._build_values({group: value})

    def test_explicit_null_fields_do_not_fall_back_to_defaults(self):
        for group, names in CONFIG_FIELDS.items():
            for name in names:
                with self.subTest(path=f"{group}.{name}"):
                    with self.assertRaisesRegex(TypeError, re.escape(f"{group}.{name}")):
                        Config._build_values({group: {name: None}})

    def test_null_mode_overrides_are_not_replaced_by_base_values(self):
        self.write_config("base", {"server": {"port": 8123}})
        self.write_config("sample", {"server": {"port": None}})
        with self.assertRaisesRegex(TypeError, r"server\.port"):
            Config.load()
        self.write_config("sample", {"server": None})
        with self.assertRaisesRegex(TypeError, "server"):
            Config.load()

    def test_integer_fields_reject_boolean_string_and_float(self):
        for group, name in (("server", "port"), ("server", "workers"), ("jwt", "exp_time"), ("mysql", "port")):
            for value in (True, False, "12", 1.5):
                with self.subTest(path=f"{group}.{name}", value=value):
                    with self.assertRaisesRegex(TypeError, re.escape(f"{group}.{name}")):
                        Config._build_values({group: {name: value}})

    def test_boolean_string_and_list_fields_keep_strict_types(self):
        cases = (
            ("app", "debug", "false"), ("paths", "relative", 0),
            ("app", "name", 123), ("redis", "url", False),
            ("server", "cors_domains", "fixture.invalid"),
            ("server", "cors_domains", ["fixture.invalid", 123]),
        )
        for group, name, value in cases:
            with self.subTest(path=f"{group}.{name}", value=value):
                with self.assertRaisesRegex(TypeError, re.escape(f"{group}.{name}")):
                    Config._build_values({group: {name: value}})

    def test_worker_minimum_uses_the_nested_error_path(self):
        for value in (0, -1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, r"server\.workers"):
                    Config._build_values({"server": {"workers": value}})
        self.assertEqual(Config._build_values({"server": {"workers": 1}})["sanic_workers"], 1)

    def test_malformed_mode_yaml_does_not_silently_fall_back(self):
        self.write_config("sample", {"app": {"name": "SampleFixture"}})
        (self.config_dir / "dev.yaml").write_text("server: [\n", encoding="utf-8")
        os.environ["MODE"] = "dev"
        with self.assertRaises(yaml.YAMLError):
            Config.load()

    def test_yaml_root_preserves_existing_empty_value_behavior(self):
        path = self.config_dir / "fixture.yaml"
        self.assertEqual(Config._read_yaml(path), {})
        for content in ("", "null", "false", "0", "[]", "{}", "''"):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                self.assertEqual(Config._read_yaml(path), {})
        for content in ("- fixture", "fixture", "1"):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(TypeError, "mapping"):
                    Config._read_yaml(path)


class ConfigurationSchemaTestCase(unittest.TestCase):
    def test_schema_and_runtime_cover_the_same_twenty_one_fields(self):
        schema = json.loads((SRC / "core/config/schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["properties"]), set(CONFIG_FIELDS))
        attributes = {item.name: item.type for item in fields(ConfigModel)}
        self.assertEqual(set(attributes), {name for group in CONFIG_FIELDS.values() for name in group.values()})
        json_types = {str: "string", int: "integer", bool: "boolean", list: "array"}
        for group, names in CONFIG_FIELDS.items():
            definition = schema["properties"][group]
            self.assertEqual(definition["type"], "object")
            self.assertIs(definition["additionalProperties"], False)
            self.assertEqual(set(definition["properties"]), set(names))
            for name, attribute in names.items():
                with self.subTest(path=f"{group}.{name}"):
                    field_schema = definition["properties"][name]
                    expected_type = get_origin(attributes[attribute]) or attributes[attribute]
                    self.assertEqual(field_schema["type"], json_types[expected_type])
                    if expected_type is list:
                        self.assertEqual(field_schema["items"]["type"], "string")
        self.assertEqual(schema["properties"]["server"]["properties"]["workers"]["minimum"], 1)

    def test_repository_yaml_keys_match_the_nested_schema(self):
        for name in ("base", "sample"):
            raw = yaml.safe_load((SRC / f"core/config/{name}.yaml").read_text(encoding="utf-8"))
            with self.subTest(file=name):
                self.assertEqual(type(raw), dict)
                self.assertTrue(set(raw) <= CONFIG_FIELDS.keys())
                for group, values in raw.items():
                    self.assertEqual(type(values), dict, group)
                    self.assertTrue(set(values) <= CONFIG_FIELDS[group].keys(), group)
                self.assertEqual(set(Config._build_values(raw)), {item.name for item in fields(ConfigModel)})


if __name__ == "__main__":
    unittest.main()
