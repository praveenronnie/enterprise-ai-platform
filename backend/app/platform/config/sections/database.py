# database configuration
from __future__ import annotations

from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):

    DB_URL: str = Field(
        min_length=1,
        description="Full database connection URL.",
    )
    DB_POOL_SIZE: int = Field(
        ge=1,
        description="Maximum connection pool size.",
    )
    DB_MAX_OVERFLOW: int = Field(
        ge=0,
        description="Maximum overflow connections beyond pool size.",
    )
    DB_ECHO: bool = Field(
        description="Log all SQL statements (debugging aid).",
    )
    DB_TIMEOUT: int = Field(
        ge=1,
        description="Connection timeout in seconds.",
    )
