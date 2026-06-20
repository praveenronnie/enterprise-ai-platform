# api configuration
from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.platform.config.sections.common import JsonList


class ApiSettings(BaseModel):

    HOST: str = Field(
        description="Bind address for the HTTP server.",
    )
    PORT: int = Field(
        ge=1,
        le=65535,
        description="Port number for the HTTP server.",
    )
    CORS_ORIGINS: JsonList = Field(
        description="Allowed CORS origins.",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        description="Whether to expose credentials via CORS.",
    )
    CORS_ALLOW_METHODS: JsonList = Field(
        description="Allowed HTTP methods for CORS.",
    )
    CORS_ALLOW_HEADERS: JsonList = Field(
        description="Allowed HTTP headers for CORS.",
    )
    API_PREFIX: str = Field(
        description="URL prefix with version.",
    )
