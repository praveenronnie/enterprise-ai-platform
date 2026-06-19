"""
Centralized application settings using Pydantic Settings v2.

Loading priority:
    1. Environment variables (highest)
    2. .env file
    3. Default values (lowest)
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings loaded from environment / .env file."""

    # ── General ──────────────────────────────────────────────────────
    APP_NAME: str = "Enterprise AI Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Server ───────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Logging ──────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # ── Paths ────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    # ── Pydantic model configuration ─────────────────────────────────
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Module-level singleton for easy import
settings: Settings = Settings()  # type: ignore[call-arg]
"""
Pre-initialised settings singleton.

Usage::

    from app.config.settings import settings
    print(settings.APP_NAME)
"""