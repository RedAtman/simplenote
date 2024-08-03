import logging
import logging.config
import os
import sys


ENV = os.getenv("ENV")
BASE_DIR: str = os.getenv("BASE_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# LOG_DIR: str = os.path.join(BASE_DIR, "logs")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 5))
LOG_FORMATTER = "standard"
LOG_FILTERS = []
formatters = {
    "simple": {
        "format": "%(asctime)s: [%(levelname)s]: %(name)s: %(message)s",
    },
    "standard": {
        "format": "%(asctime)s:[%(levelname)s]:%(pathname)s:%(lineno)d:%(funcName)s: %(message)s",
    },
    "relpath": {
        "format": "%(asctime)s: [%(levelname)s]: %(name)s: %(message)s",
    },
}
filters = {
    "default": {"()": logging.Filter},
    "relpath": {"()": logging.Filter},
    "json": {"()": logging.Filter},
    "color": {"()": logging.Filter},
    "debug": {"()": logging.Filter},
    "info": {"()": logging.Filter},
    "warning": {"()": logging.Filter},
    "error": {"()": logging.Filter},
    "critical": {"()": logging.Filter},
}
if ENV == "development":
    from . import lexers

    LOG_FORMATTER = "relpath"
    LOG_FILTERS = [
        "relpath",
        "json",
        "color",
    ]
    formatters["relpath"] = {
        "format": "[%(levelname)s]%(relpath)s:%(lineno)d:%(funcName)s: %(message)s",
    }
    _filters = {
        "relpath": {"()": "utils.logger.filters.RelPathFilter"},
        "json": {
            "()": "utils.logger.filters.JsonFilter",
            "lexer": lexers.json,
        },
        "color": {"()": "utils.logger.filters.ColorFilter"},
        "debug": {"()": "utils.logger.filters.LevelMatchFilter", "level": "debug", "operator": "eq"},
        "info": {"()": "utils.logger.filters.LevelMatchFilter", "level": "info", "operator": "eq"},
        "warning": {"()": "utils.logger.filters.LevelMatchFilter", "level": "warning", "operator": "eq"},
        "error": {"()": "utils.logger.filters.LevelMatchFilter", "level": "error", "operator": "eq"},
        "critical": {"()": "utils.logger.filters.LevelMatchFilter", "level": "critical", "operator": "eq"},
    }
    filters = dict(filters, **_filters)


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": formatters,
    "filters": filters,
    "handlers": {
        "default": {
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.StreamHandler",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/default.log",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": LOG_BACKUP_COUNT,
            # "encoding": "utf8",
            # "delay": False,
            # "utc": False,
            # "atTime": None,
            # "errors": None,
            "level": "DEBUG",
            "formatter": "standard",
            "filters": ["default"],
        },
        "info": {
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.StreamHandler",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/info.log",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": LOG_BACKUP_COUNT,
            # "encoding": "utf8",
            # "delay": False,
            # "utc": False,
            # "atTime": None,
            # "errors": None,
            "level": "INFO",
            "formatter": "standard",
            # 'maxBytes': 5*1024*1024,
            "filters": ["info"],
        },
        "warning": {
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.StreamHandler",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/warning.log",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": LOG_BACKUP_COUNT,
            # "encoding": "utf8",
            # "delay": False,
            # "utc": False,
            # "atTime": None,
            # "errors": None,
            "level": "WARNING",
            "formatter": "standard",
            # 'maxBytes': 5*1024*1024,
            "filters": ["warning"],
        },
        "error": {
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.StreamHandler",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/error.log",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": LOG_BACKUP_COUNT,
            # "encoding": "utf8",
            # "delay": False,
            # "utc": False,
            # "atTime": None,
            # "errors": None,
            "level": "ERROR",
            "formatter": "standard",
            # 'maxBytes': 5*1024*1024,
            "filters": ["error"],
        },
        "critical": {
            "level": "CRITICAL",
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.StreamHandler",
            # "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/critical.log",
            # "when": "midnight",
            # "interval": 1,
            # "backupCount": LOG_BACKUP_COUNT,
            # "encoding": "utf8",
            # "delay": False,
            # "utc": False,
            # "atTime": None,
            # "errors": None,
            "level": "CRITICAL",
            "formatter": "standard",
            # 'maxBytes': 5*1024*1024,
            "filters": ["critical"],
        },
        "critical_mail": {
            "class": "logging.handlers.SMTPHandler",
            "level": "CRITICAL",
            "formatter": "standard",
            "mailhost": "localhost",
            "fromaddr": "xxx@domain.com",
            "toaddrs": ["xxx@domain.com", "xxx@domain.com"],
            "subject": "Critical error with application name",
            "filters": ["critical"],
        },
        "console": {
            # Default is stderr
            # "stream": "ext://sys.stdout",
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": LOG_FORMATTER,
            "filters": LOG_FILTERS,
        },
    },
    "loggers": {
        # root logger
        "": {
            "handlers": [
                # "default",
                # "info",
                # "warning",
                # "error",
                # "critical",
                # Keep console at the end. for colored output only at stdout.
                "console",
            ],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "script": {"handlers": ["default"], "level": "INFO", "propagate": False},
        # if __name__ == '__main__'
        "__main__": {
            "handlers": ["default", "console", "info", "warning", "critical", "error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": [
                "default",
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


logging.config.dictConfig(LOG_CONFIG)
logging.info(f"Logging is configured. ENV: {ENV}, FORMATTER: {LOG_FORMATTER}, LOG_FILTERS: {LOG_FILTERS}")


if __name__ == "__main__":
    logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    logger.debug("Logging is configured.")
    logger.debug("log level: debug")
    logger.info("log level: info")
    logger.warning("log level: warning")
    logger.error("log level: error")
    logger.exception("log level: exception")
    logger.critical("log level: critical")
    logger.info({"a": 1, "b": "-" * 80, "c": {"d": 3, "e": 4, "f": {"g": 5, "h": 6}}})

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.debug("sqlalchemy debug")
    sqlalchemy_logger.info("sqlalchemy info")
    sqlalchemy_logger.warning("sqlalchemy warning")
    sqlalchemy_logger.error(sqlalchemy_logger.__dict__)
