import logging
import os


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
