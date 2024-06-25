import functools
import logging
import os
from typing import Any, Callable, Optional


BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# class _ColorfulFormatter(logging.Formatter):

#     def __init__(self, *args, **kwargs):
#         self._root_name = kwargs.pop("root_name") + "."
#         self._abbrev_name = kwargs.pop("abbrev_name", "")
#         if len(self._abbrev_name):
#             self._abbrev_name = self._abbrev_name + "."
#         super(_ColorfulFormatter, self).__init__(*args, **kwargs)

#     def formatMessage(self, record):
#         record.name = record.name.replace(self._root_name, self._abbrev_name)
#         log = super(_ColorfulFormatter, self).formatMessage(record)
#         if record.levelno == logging.WARNING:
#             prefix = colored("WARNING", "red", attrs=["blink"])
#         elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
#             prefix = colored("ERROR", "red", attrs=["blink", "underline"])
#         else:
#             return log
#         return prefix + " " + log


class RelativePathFormatter(logging.Formatter):

    def format(self, record) -> str:
        record.relpath = record.pathname.replace(f"{BASE_DIR}/", "", 1)
        return super().format(record)


from enum import IntEnum


_PREFIX = "\033["
_SUFFIX = "\033[0m"
# NC = "\x1b[0m"  # No Color


class Color(IntEnum):
    DEFAULT = 29
    GREY = 30  # 灰色
    RED = 31  # 红色
    GREEN = 32  # 绿色
    YELLOW = 33  # 黄色
    BLUE = 34  # 蓝色
    PINK = 35  # 紫色
    CYAN = 36  # 青色
    WHITE = 37  # 白色
    # Foreground:
    GREY_OK = 90
    RED_OK = 91
    GREEN_OK = 92
    YELLOW_OK = 93
    BLUE_OK = 94
    PINK_OK = 95
    CYAN_OK = 96
    WHITE_OK = 97
    # Background:
    GREY_BG = 100
    RED_BG = 101
    GREEN_BG = 102
    YELLOW_BG = 103
    BLUE_BG = 104
    PINK_BG = 105
    CYAN_BG = 106
    WHITE_BG = 107
    # Formatting
    BOLD = 1
    ITALIC = 3
    UNDERLINE = 4

    def format(
        self,
        text: str,
        bold=False,
        underline=False,
        italic=False,
        bg: Optional[int] = None,
    ):
        c = self
        if bold:
            c = f"1;{c}"
        if italic:
            c = f"3;{c}"
        if underline:
            c = f"4;{c}"
        if bg:
            c = f"{c};{bg}"
        return f"{_PREFIX}{c}m{text}{_SUFFIX}"


class LevelColor(IntEnum):
    DEFAULT = Color.DEFAULT
    NONE = Color.DEFAULT
    DEBUG = Color.CYAN
    INFO = Color.GREEN
    WARNING = Color.YELLOW
    ERROR = Color.RED
    CRITICAL = Color.PINK
    EXCEPTION = Color.RED


from pprint import pformat


class ColorFormatter(logging.Formatter):
    # TODO: Currently, configuration is only supported in one formatter.

    FORMAT_PATTERN = f"[%(levelname)s]%(pathname)s:%(lineno)d: %(funcName)s: %(message)s"

    def __init__(self, *args, lexer: Callable[..., Any] = pformat, **kwargs):
        super().__init__(*args, **kwargs)
        self.lexer: Callable[..., Any] = lexer

    def format(self, record: logging.LogRecord) -> str:
        level_color_num = getattr(LevelColor, record.levelname, LevelColor.DEFAULT)
        record.levelname = Color(level_color_num).format(record.levelname, bold=True)
        record.pathname = Color.GREY_OK.format(record.pathname)
        # if record.msg and isinstance(record.msg, (dict, list)):
        #     record.msg = "\n" + self.lexer(record.msg)
        # else:
        #     record.msg = Color(level_color_num).format(record.msg)
        record.msg = Color(level_color_num).format(record.msg)
        return super().format(record)


def json_wrap(fuc: Callable[..., Any]):
    @functools.wraps(fuc)
    def inner(self: logging.Logger, msg, *args, **kwargs):
        level_color: LevelColor = getattr(LevelColor, fuc.__name__.upper(), LevelColor.DEFAULT)
        filename, lineno, name, sinfo = self.findCaller(stack_info=True)
        prefix = f"[{Color(level_color).format('JSON')}]: {Color.GREY_OK.format(filename)}:{lineno}: {name}:"
        # Print the stack trace
        if isinstance(msg, (list, dict)):
            # print(
            #     f"{prefix}\n{ColorFormatter.format_msg(msg)}",
            #     # end='',
            # )
            self._log(level_color, f"{prefix}\n{ColorFormatter.format_msg(msg)}", (), **kwargs)
            return
        msg = f"{prefix} {Color(level_color).format(msg)}"
        # print(msg)
        self._log(level_color, msg, (), **kwargs)

    return inner


# Second method
# for level in ("debug", "info", "warning", "error", "exception", "critical"):
#     setattr(logging.Logger, level, json_wrap(getattr(logging.Logger, level)))

if __name__ == "__main__":
    print(Color.RED.format("hello"))
    print(Color.RED.format("hello", bold=True))
    print(Color.PINK_OK.format("hello", underline=True, italic=True))
    print(Color.BLUE.format("hello", bold=True, underline=True))
    print(Color.RED.format("hello", bg=Color.BLUE_BG))

    import logging.config

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "color": {
                # First method
                "()": ColorFormatter,
                "format": ColorFormatter.FORMAT_PATTERN,
            },
            "relative": {
                "()": RelativePathFormatter,
                "format": "%(relpath)s:%(lineno)d: %(funcName)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "color",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger()  # type: ignore
    # logger.setLevel(logging.WARNING)
    logger.debug("log level: debug")
    logger.info("log level: info")
    logger.warning("log level: warning")
    logger.error("log level: error")
    logger.exception("log level: exception")
    logger.critical("log level: critical")
    logger.debug({"a": 1, "b": "-" * 80, "c": {"d": 3, "e": 4, "f": {"g": 5, "h": 6}}})
    logger.info({"a": 1, "b": "-" * 80, "c": {"d": 3, "e": 4, "f": {"g": 5, "h": 6}}})
    logger.debug([])
    logger.info({})

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.debug("sqlalchemy debug")
    sqlalchemy_logger.info("sqlalchemy info")
    sqlalchemy_logger.warning("sqlalchemy warning")
    sqlalchemy_logger.error(sqlalchemy_logger.__dict__)
