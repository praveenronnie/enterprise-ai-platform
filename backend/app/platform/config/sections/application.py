# application configuration
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ApplicationSettings(BaseModel):

    APP_NAME: str = Field(
        description="Human-readable product name.",
    )
    APP_VERSION: str = Field(
        description="Semantic version of the application.",
    )
    DEBUG: bool = Field(
        description="Enable debug mode (live reload, verbose logging, Swagger).",
    )
    PROJECT_ROOT: Path = Field(
        description="Absolute path to the project root directory.",
    )
