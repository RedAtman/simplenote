import logging
import logging.config
import os


ENV = os.getenv("ENV", "development")
FORMATTER = "color" if ENV == "development" else "standard"
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
BACKUP_COUNT = 9

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s: [%(levelname)s]: %(name)s: %(message)s",
        },
        "standard": {
            "format": "%(asctime)s:[%(levelname)s]:%(pathname)s:%(lineno)d:%(funcName)s: %(message)s",
        },
        # "color": {
        #     "class": "utils.logger.utils.ColorFormatter",
        #     "format": "[%(levelname)s]%(relpath)s:%(lineno)d:%(funcName)s: %(message)s",
        # },
    },
    "filters": {
        # "default": {"()": logging.Filter},
        # "relpath": {"()": "utils.logger.utils.RelPathFilter"},
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            # 'class': 'logging.StreamHandler',
            "class": "logging.handlers.TimedRotatingFileHandler",
            # "filename": f"{LOG_DIR}/default.log",
            "filename": "%s/default.log" % LOG_DIR,
            "when": "midnight",
            "backupCount": BACKUP_COUNT,
            "encoding": "utf8",
            # "filters": ["default"],
        },
        "info": {
            "level": "INFO",
            "formatter": "standard",
            # Default is stderr
            # "stream": "ext://sys.stdout",
            # "class": "logging.StreamHandler",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": BACKUP_COUNT,
            # 'maxBytes': 5*1024*1024,
            # "filename": f"{LOG_DIR}/info.log",
            "filename": "%s/info.log" % LOG_DIR,
            "encoding": "utf8",
            # 'filters': ['default'],
        },
        "warning": {
            "level": "WARNING",
            "formatter": "standard",
            # Default is stderr
            # "stream": "ext://sys.stdout",
            # "class": "logging.StreamHandler",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": BACKUP_COUNT,
            # 'maxBytes': 5*1024*1024,
            "encoding": "utf8",
            # "filename": f"{LOG_DIR}/warning.log",
            "filename": "%s/warning.log" % LOG_DIR,
            # "filters": ["default"],
        },
        "error": {
            "level": "ERROR",
            "formatter": "standard",
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": BACKUP_COUNT,
            # 'maxBytes': 5*1024*1024,
            # "filename": f"{LOG_DIR}/error.log",
            "filename": "%s/error.log" % LOG_DIR,
            "encoding": "utf8",
            # "filters": ["default"],
        },
        "critical": {
            "level": "CRITICAL",
            "formatter": "standard",
            # Default is stderr
            # 'stream': 'ext://sys.stdout',
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "midnight",
            "backupCount": BACKUP_COUNT,
            # 'maxBytes': 5*1024*1024,
            # "filename": f"{LOG_DIR}/critical.log",
            "filename": "%s/critical.log" % LOG_DIR,
            "encoding": "utf8",
            # "filters": ["default"],
        },
        "critical_mail": {
            "level": "CRITICAL",
            "formatter": "standard",
            "class": "logging.handlers.SMTPHandler",
            "mailhost": "localhost",
            "fromaddr": "xxx@domain.com",
            "toaddrs": ["xxx@domain.com", "xxx@domain.com"],
            "subject": "Critical error with application name",
            # "filters": ["default"],
        },
        "console": {
            "level": "DEBUG",
            # "formatter": FORMATTER,
            "formatter": "standard",
            # Default is stderr
            # "stream": "ext://sys.stdout",
            "class": "logging.StreamHandler",
            # "filters": ["relpath"],
        },
    },
    "loggers": {
        # root logger
        "": {
            "handlers": [
                # "default",
                "info",
                "warning",
                "error",
                "critical",
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


logging.config.dictConfig(LOGGING_CONFIG)


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
