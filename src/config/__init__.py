import os
import logging
import importlib
from dotenv import load_dotenv
load_dotenv()

class Config:
    _instance = None

    def __new__(cls) :
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def __getattr__(self, name):
        return getattr(self.config, name)

    def _load_config(self):
        """
        加载配置
        """
        mode = os.environ.get('MODE', 'SAMPLE').lower()
        try:
            custom_config_module = importlib.import_module(f'.{mode}', package=__package__)
            self.config = custom_config_module
            logging.info(f"[Config] - [{mode}] is loaded")
        except ImportError:
            logging.error(f"[Config] - [{mode}] cannot be imported, falling back to [SAMPLE]")
            from . import sample
            self.config = sample
