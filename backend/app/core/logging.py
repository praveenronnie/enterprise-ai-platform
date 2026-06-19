"""
Centralised logging configuration.

Configures Python's standard ``logging`` module based on application
settings.  Call ``setup_logging()`` once at application startup.
"""

from __future__ import annotations

import logging
import sys
from typing import NoReturn

from app.config.settings import settings


def setup_logging() -> None:
    """
    Configure the root logger based on application settings.

    Output is sent to stdout with the configured format and level.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    # Remove default handlers to avoid duplicate logs.
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers if not debugging.
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger for the given *name*.

    Typical usage::

        logger = get_logger(__name__)
    """
    return logging.getLogger(name)