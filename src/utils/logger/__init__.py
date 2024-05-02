import os
import logging

class Logger:
    _instance = None

    def __new__(cls) -> logging:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_config()
            logging.info(f"[Utils] - [Logger] is loaded")
        return cls._instance
    
    def __getattr__(self, name):
        return getattr(self.LoggerInstance, name)

    def load_config(self):
        """
        加载配置
        """
        log_path = os.environ.get('LOG_PATH', 'logs')

        from . import base
        LoggerInstance = base.setupLogger("Logger", log_path, "MIDNIGHT", logging.INFO)
        self.LoggerInstance = LoggerInstance