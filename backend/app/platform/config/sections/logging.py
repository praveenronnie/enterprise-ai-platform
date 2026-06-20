# Logging configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class LoggingSettings(BaseModel):

    LOG_LEVEL: str = Field(
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Root logger level.",
    )
    LOG_FORMAT: str = Field(
        description="Python logging format string.",
    )
    LOG_SILENCE_THIRD_PARTY: bool = Field(
        description="Suppress verbose third-party loggers when not in debug mode.",
    )
