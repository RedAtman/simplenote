from logging import LogRecord, StreamHandler
from pprint import pformat
from typing import Any, Callable, Dict, Tuple


__all__ = ["JsonHandler"]


class JsonHandler(StreamHandler):

    def __init__(self, *args: Tuple[Any, ...], lexer: Callable[..., Any] = pformat, **kwargs: Dict[str, Any]):
        super().__init__(*args, **kwargs)
        self.lexer: Callable[..., Any] = lexer

    def emit(self, record: LogRecord) -> None:
        if record.msg and isinstance(record.msg, (dict, list)):
            record.msg = self.lexer(record.msg)
        super().emit(record)
        # _dict = {}
        # for attr in filter(lambda attr: not attr.endswith("__"), dir(record)):
        #     _dict[attr] = record.__getattribute__(attr)
        # del _dict["getMessage"]
        # pprint(_dict)


if __name__ == "__main__":
    import logging.config

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "json": {
                    "level": "DEBUG",
                    # "class": "base.__.__getattribute__.JsonHandler",
                    "()": JsonHandler,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["json"],
                    "level": "DEBUG",
                },
            },
        }
    )
    logger = logging.getLogger()
    logger.debug("Hello, world!")
    # logger.info("Hello, world!")
    logger.info(logger.__dict__)
    # logger.warning("Hello, world!")
    # logger.error("Hello, world!")
    # logger.critical("Hello, world!")
    # logger.exception("Hello, world!")
