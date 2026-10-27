import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, patch, sentinel


SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class DatabaseConfigurationTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from core.config import Config
            from infra import database
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f"Database dependencies are unavailable: {exc}") from exc
        cls.database = database
        cls.config = Config(app="configured_app", mysql_host="configured-db", mysql_database_name="configured_schema")

    def test_http_registration_uses_each_supplied_config(self):
        configs = [self.config, replace(self.config, app="other_app", mysql_host="other-db")]
        with (
            patch.object(self.database, "load_config", side_effect=AssertionError("Unexpected default config load")),
            patch("tortoise.contrib.sanic.register_tortoise") as register,
        ):
            for config in configs:
                with self.subTest(app=config.app):
                    self.database.register_database(sentinel.server, config)
                    register.assert_called_with(
                        sentinel.server,
                        config=self.database.build_tortoise_orm_config(config),
                        generate_schemas=False,
                    )
                    self.assertEqual(register.call_args.kwargs["config"]["connections"]["default"]["credentials"]["host"], config.mysql_host)

    def test_migrations_and_runtime_share_model_metadata(self):
        from core.persistence import ORM_MODEL_MODULES

        self.assertEqual(ORM_MODEL_MODULES, (
            "domains.identity_access.models", "domains.audit.models",
        ))
        runtime = self.database.build_tortoise_orm_config(self.config)
        migration = self.database.build_tortoise_orm_config(self.config, include_aerich=True)
        self.assertEqual(runtime["apps"][self.config.app]["models"], list(ORM_MODEL_MODULES))
        self.assertEqual(migration["apps"][self.config.app]["models"], [*ORM_MODEL_MODULES, "aerich.models"])

    async def test_initialization_uses_supplied_config_without_creating_schema(self):
        with (
            patch.object(self.database, "load_config", side_effect=AssertionError("Unexpected default config load")),
            patch.object(self.database.Tortoise, "init", new_callable=AsyncMock) as initialize,
            patch.object(self.database.Tortoise, "generate_schemas", new_callable=AsyncMock) as generate,
            patch.dict(os.environ, {"DB_AUTO_SCHEMA": "0"}),
        ):
            await self.database.init_database(self.config)
        initialize.assert_awaited_once_with(config=self.database.build_tortoise_orm_config(self.config))
        generate.assert_not_awaited()

    async def test_schema_generation_remains_explicitly_opt_in(self):
        with (
            patch.object(self.database.Tortoise, "init", new_callable=AsyncMock),
            patch.object(self.database.Tortoise, "generate_schemas", new_callable=AsyncMock) as generate,
            patch.dict(os.environ, {"DB_AUTO_SCHEMA": "true"}),
        ):
            await self.database.init_database(self.config)
        generate.assert_awaited_once_with(safe=True)

    async def test_close_database_closes_connections(self):
        with patch.object(self.database.Tortoise, "close_connections", new_callable=AsyncMock) as close:
            await self.database.close_database()
        close.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
