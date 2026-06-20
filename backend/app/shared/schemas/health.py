# Health check endpoint
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):

    status: str = Field(default="ok", description="Service health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the check",
    )
    version: str = Field(default="0.1.0", description="Application version")