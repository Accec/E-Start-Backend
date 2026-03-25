from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER
from infra.logging import Logger


def setup_application_loggers():
    Logger.setup_root_logger()

    # Sanic configures its own named loggers during import/application setup.
    # Strip their handlers so they emit through the same root logger as the
    # rest of the application.
    for logger_name in ("sanic.root", "sanic.error", "sanic.access", "sanic.server", "sanic.websockets"):
        Logger.mount_logger(logger_name)

    for logger_name in (SERVER_LOGGER, SCHEDULER_LOGGER, API_LOGGER, TASK_LOGGER, JOB_LOGGER):
        Logger.mount_logger(logger_name)
