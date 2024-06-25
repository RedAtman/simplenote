import logging
import operator as _operator
import os
from pprint import pformat
import sys
from typing import Any, Callable

from .formatters import Color, LevelColor


__all__ = ["RelativePathFilter", "RelPathFilter", "JsonFilter", "ColorFilter", "LevelMatchFilter"]


logger = logging.getLogger(__name__)


class RelativePathFilter(logging.Filter):

    def filter(self, record):
        pathname = record.pathname
        record.relativepath = None
        abs_sys_paths = map(os.path.abspath, sys.path)
        for path in sorted(abs_sys_paths, key=len, reverse=True):
            if not path.endswith(os.sep):
                path += os.sep
            if pathname.startswith(path):
                record.relativepath = os.path.relpath(pathname, path)
                break
        return True


class RelPathFilter(logging.Filter):

    def filter(self, record: logging.LogRecord):
        # record.relpath = record.pathname.replace(f'{BASE_DIR}/', '', 1)
        record.relpath = os.path.relpath(record.pathname)
        return True


class JsonFilter(logging.Filter):
    def __init__(self, *args, lexer: Callable[..., Any] = pformat, **kwargs):
        super().__init__(*args, **kwargs)
        self.lexer: Callable[..., Any] = lexer

    def filter(self, record: logging.LogRecord):
        if record.msg and isinstance(record.msg, (dict, list)):
            record.msg = self.lexer(record.msg)
        return True


class ColorFilter(logging.Filter):
    # TODO: Currently, configuration is only supported in one formatter.

    FORMAT_PATTERN = f"[%(levelname)s]%(pathname)s:%(lineno)d: %(funcName)s: %(message)s"

    def __init__(self, *args, lexer: Callable[..., Any] = pformat, **kwargs):
        super().__init__(*args, **kwargs)
        self.lexer: Callable[..., Any] = lexer

    def filter(self, record: logging.LogRecord) -> bool:
        level_color_num = getattr(LevelColor, record.levelname, LevelColor.DEFAULT)
        record.levelname = Color(level_color_num).format(record.levelname, bold=True)
        record.pathname = Color.GREY_OK.format(record.pathname)
        # if record.msg and isinstance(record.msg, (dict, list)):
        #     record.msg = "\n" + self.lexer(record.msg)
        # else:
        #     record.msg = Color(level_color_num).format(record.msg)
        record.msg = Color(level_color_num).format(record.msg)
        return True


class LevelMatchFilter(logging.Filter):

    def __init__(self, level: str, operator: str):
        self.level: str = level
        self.levelno: int = logging.getLevelName(level.upper())
        # Comparison Operations: eq, ne, lt, le, gt, ge
        operator_fuc = getattr(_operator, operator)
        if not operator_fuc:
            raise ValueError(f"Invalid operator: {operator}, must be one of: eq, ne, lt, le, gt, ge")
        assert isinstance(operator_fuc, type(_operator.eq))
        self.operator = operator_fuc

    def filter(self, record: logging.LogRecord):
        if self.operator(record.levelno, self.levelno):
            return True
        return False


if __name__ == "__main__":
    import logging.config

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "filters": {
            "debug": {"()": LevelMatchFilter, "level": "debug", "operator": "eq"},
            "info": {"()": LevelMatchFilter, "level": "info", "operator": "eq"},
            "warning": {"()": LevelMatchFilter, "level": "warning", "operator": "eq"},
        },
        "handlers": {
            "debug": {
                "class": "logging.FileHandler",
                "filename": "debug.log",
                "level": "DEBUG",
                "filters": ["debug"],
                "formatter": "simple",
            },
            "info": {
                "class": "logging.FileHandler",
                "filename": "info.log",
                "level": "INFO",
                "filters": ["info"],
                "formatter": "simple",
            },
            "warning": {
                "class": "logging.FileHandler",
                "filename": "warning.log",
                "level": "WARNING",
                "filters": ["warning"],
                "formatter": "simple",
            },
        },
        "root": {
            "handlers": ["debug", "info", "warning"],
            "level": "DEBUG",
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("test")
    logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
