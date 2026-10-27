import logging
import os

from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER


class Logger:
    @staticmethod
    def setup_root_logger():
        log_path = os.environ.get("LOG_PATH", "logs")

        from . import base

        return base.setup_root_logger(log_path, "MIDNIGHT", logging.INFO)

    @staticmethod
    def mount_logger(logger_name):
        from . import base

        return base.mount_logger(logger_name, logging.INFO)


def setup_application_loggers():
    Logger.setup_root_logger()

    # Sanic configures its own named loggers during import/application setup.
    # Strip their handlers so they emit through the same root logger as the
    # rest of the application.
    for logger_name in ("sanic.root", "sanic.error", "sanic.access", "sanic.server", "sanic.websockets"):
        Logger.mount_logger(logger_name)

    for logger_name in (SERVER_LOGGER, SCHEDULER_LOGGER, API_LOGGER, TASK_LOGGER, JOB_LOGGER):
        Logger.mount_logger(logger_name)
