from core.constants import API_LOGGER, JOB_LOGGER, SCHEDULER_LOGGER, SERVER_LOGGER, TASK_LOGGER
from infra.logging import Logger


def setup_application_loggers():
    for logger_name in (SERVER_LOGGER, SCHEDULER_LOGGER, API_LOGGER, TASK_LOGGER, JOB_LOGGER):
        Logger.setup_logger(logger_name)
