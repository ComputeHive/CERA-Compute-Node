import logging
import os
from datetime import datetime

_LOGS_DIR = "logs"
_MAX_BYTES = 3 * 1024 * 1024
_FMT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


class FileHandler(logging.FileHandler):
    def __init__(self, filename: str, max_bytes: int, **kwargs):
        super().__init__(filename, **kwargs)
        self.max_bytes = max_bytes

    def emit(self, record: logging.LogRecord):
        try:
            if self.stream.tell() >= self.max_bytes:
                return
        except Exception:
            pass
        super().emit(record)


def _make_file_handler() -> FileHandler:
    os.makedirs(_LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime(_DATE_FMT)
    path = os.path.join(_LOGS_DIR, f"log_{timestamp}.log")
    handler = FileHandler(path, _MAX_BYTES, encoding="utf-8")
    handler.setFormatter(logging.Formatter(fmt=_FMT, datefmt=_DATE_FMT))
    return handler


def _make_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=_FMT, datefmt=_DATE_FMT))
    return handler


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    logger.addHandler(_make_file_handler())
    logger.addHandler(_make_console_handler())
    logger.propagate = False
    return logger
