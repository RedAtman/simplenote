from logging import LogRecord, StreamHandler

from .output import output


class JsonHandler(StreamHandler):

    def emit(self, record: LogRecord) -> None:
        msg = output(record.msg)
        print(msg)
        # msg = self.format(record)
        # output(msg)
        # stream = self.stream
        # print('stream', stream)
        # pprint(record.__dict__)
        # output(record.__dict__)
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
