import logging

_configured_loggers = set()


def get_logger(name: str) -> logging.Logger:
    short_name = name.split(".")[-1].strip("_")
    if short_name in _configured_loggers:
        return logging.getLogger(short_name)

    logger = logging.getLogger(short_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _configured_loggers.add(short_name)

    return logger
