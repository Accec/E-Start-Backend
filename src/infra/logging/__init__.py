import logging
import os


class Logger:
    @staticmethod
    def setup_logger(logger_name):
        log_path = os.environ.get("LOG_PATH", "logs")

        from . import base

        base.setup_logger(logger_name, log_path, "MIDNIGHT", logging.INFO)
