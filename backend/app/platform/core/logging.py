# Logging configuration
from __future__ import annotations

import logging
import sys
from typing import NoReturn

from backend.app.platform.config.settings import Settings


def setup_logging(settings: Settings | None = None) -> None:
    if settings is not None:
        log_level = settings.LOG_LEVEL.upper()
        log_format = settings.LOG_FORMAT
        debug = settings.DEBUG
    else:
        log_level = "INFO"
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        debug = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    if not debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
