import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def snapshot_logger(logger: logging.Logger):
    return {
        "handlers": list(logger.handlers),
        "level": logger.level,
        "propagate": logger.propagate,
    }


def restore_logger(logger: logging.Logger, state):
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    for handler in state["handlers"]:
        logger.addHandler(handler)

    logger.setLevel(state["level"])
    logger.propagate = state["propagate"]


class LoggingConfigurationTestCase(unittest.TestCase):
    def test_application_loggers_mount_to_root_logger(self):
        from app.bootstrap.logging import setup_application_loggers
        from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER

        root_logger = logging.getLogger()
        app_loggers = [logging.getLogger(name) for name in (SERVER_LOGGER, SCHEDULER_LOGGER, API_LOGGER, TASK_LOGGER, JOB_LOGGER)]
        sanic_logger = logging.getLogger("sanic.root")

        root_state = snapshot_logger(root_logger)
        app_states = {logger.name: snapshot_logger(logger) for logger in app_loggers}
        sanic_state = snapshot_logger(sanic_logger)
        previous_log_path = os.environ.get("LOG_PATH")

        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LOG_PATH"] = tmp_dir
            sanic_logger.addHandler(logging.StreamHandler())
            try:
                setup_application_loggers()

                self.assertEqual(len(root_logger.handlers), 2)
                self.assertFalse(root_logger.propagate)

                for logger in app_loggers:
                    self.assertEqual(logger.handlers, [])
                    self.assertTrue(logger.propagate)

                self.assertEqual(sanic_logger.handlers, [])
                self.assertTrue(sanic_logger.propagate)
            finally:
                if previous_log_path is None:
                    os.environ.pop("LOG_PATH", None)
                else:
                    os.environ["LOG_PATH"] = previous_log_path

                restore_logger(root_logger, root_state)
                for logger in app_loggers:
                    restore_logger(logger, app_states[logger.name])
                restore_logger(sanic_logger, sanic_state)

    def test_create_app_does_not_reinstall_sanic_default_handlers(self):
        try:
            from sanic import Sanic
            from app.bootstrap.application import create_app
            from app.bootstrap.logging import setup_application_loggers
            from core.config import load_config
        except ModuleNotFoundError as exc:
            self.skipTest(f"Sanic dependencies are unavailable: {exc}")

        root_logger = logging.getLogger()
        sanic_root_logger = logging.getLogger("sanic.root")
        sanic_error_logger = logging.getLogger("sanic.error")
        sanic_access_logger = logging.getLogger("sanic.access")
        sanic_server_logger = logging.getLogger("sanic.server")

        logger_states = {
            "root": snapshot_logger(root_logger),
            "sanic.root": snapshot_logger(sanic_root_logger),
            "sanic.error": snapshot_logger(sanic_error_logger),
            "sanic.access": snapshot_logger(sanic_access_logger),
            "sanic.server": snapshot_logger(sanic_server_logger),
        }
        previous_log_path = os.environ.get("LOG_PATH")

        with tempfile.TemporaryDirectory() as tmp_dir:
            os.environ["LOG_PATH"] = tmp_dir
            try:
                Sanic._app_registry.pop(load_config().app, None)
                setup_application_loggers()
                create_app(load_config())

                self.assertEqual(sanic_root_logger.handlers, [])
                self.assertEqual(sanic_error_logger.handlers, [])
                self.assertEqual(sanic_access_logger.handlers, [])
                self.assertEqual(sanic_server_logger.handlers, [])
                self.assertTrue(sanic_root_logger.propagate)
            finally:
                if previous_log_path is None:
                    os.environ.pop("LOG_PATH", None)
                else:
                    os.environ["LOG_PATH"] = previous_log_path

                restore_logger(root_logger, logger_states["root"])
                restore_logger(sanic_root_logger, logger_states["sanic.root"])
                restore_logger(sanic_error_logger, logger_states["sanic.error"])
                restore_logger(sanic_access_logger, logger_states["sanic.access"])
                restore_logger(sanic_server_logger, logger_states["sanic.server"])
                Sanic._app_registry.pop(load_config().app, None)


if __name__ == "__main__":
    unittest.main()
