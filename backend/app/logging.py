import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_configured_loggers = set()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to logs/<module_name>.log
    Ensures each logger is configured only once.
    """
    if name in _configured_loggers:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    name = name.split(".")[-1]
    name = name.lstrip("_").rstrip("_")
    log_file = LOG_DIR / f"{name}.log"

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    _configured_loggers.add(name)

    return logger
