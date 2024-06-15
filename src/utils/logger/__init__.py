import os
import logging

class Logger:

    @staticmethod
    def setupLogger(logger):
        """
        setupLogger
        """
        log_path = os.environ.get('LOG_PATH', 'logs')

        from . import base
        base.setupLogger(logger, log_path, "MIDNIGHT", logging.INFO)