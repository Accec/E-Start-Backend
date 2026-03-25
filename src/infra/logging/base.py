import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler


class RetimedRotatingFileHandler(TimedRotatingFileHandler):
    def getFilesToDelete(self):
        directory_name, _ = os.path.split(self.baseFilename)
        file_names = os.listdir(directory_name)
        result = []
        for file_name in file_names:
            if self.extMatch.match(file_name):
                result.append(os.path.join(directory_name, file_name))
        if len(result) < self.backupCount:
            return []
        result.sort()
        return result[: len(result) - self.backupCount]


def split_file_name(filename):
    file_path = filename.split("default.log.")
    return "".join(file_path)


def build_suffix_pattern(when: str):
    suffix_patterns = {
        "S": r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(.log)$",
        "M": r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(.log)$",
        "H": r"^\d{4}-\d{2}-\d{2}_\d{2}(.log)$",
        "D": r"^\d{4}-\d{2}-\d{2}(.log)$",
        "MIDNIGHT": r"^\d{4}-\d{2}-\d{2}(.log)$",
        "W": r"^\d{4}-\d{2}-\d{2}(.log)$",
    }
    return suffix_patterns[when]


def clear_handlers(logger_object: logging.Logger) -> None:
    for handler in list(logger_object.handlers):
        logger_object.removeHandler(handler)
        handler.close()


def build_handlers(logs_path: str, when: str) -> list[logging.Handler]:
    log_file_path = f"{logs_path}/default.log"

    logger_handler = RetimedRotatingFileHandler(
        filename=log_file_path,
        when=when,
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    logger_handler.namer = split_file_name
    logger_handler.suffix = f"{logger_handler.suffix}.log"
    # TimedRotatingFileHandler only cleans files that match extMatch, so the
    # suffix format and the compiled pattern must stay in sync.
    logger_handler.extMatch = re.compile(build_suffix_pattern(when), re.ASCII)

    logger_formatter = logging.Formatter(
        "[%(asctime)s] [%(process)d] [%(levelname)s] - %(name)s.%(module)s.%(funcName)s "
        "(%(filename)s:%(lineno)d) - %(message)s"
    )
    stream_handler = logging.StreamHandler()

    logger_handler.setFormatter(logger_formatter)
    stream_handler.setFormatter(logger_formatter)

    return [logger_handler, stream_handler]


def setup_root_logger(logs_path: str, when: str, level: int) -> logging.Logger:
    logger_object = logging.getLogger()
    clear_handlers(logger_object)

    for handler in build_handlers(logs_path, when):
        logger_object.addHandler(handler)

    logger_object.setLevel(level)
    logger_object.propagate = False
    return logger_object


def mount_logger(log_name: str, level: int) -> logging.Logger:
    logger_object = logging.getLogger(log_name)
    clear_handlers(logger_object)
    logger_object.setLevel(level)
    logger_object.propagate = True
    return logger_object
