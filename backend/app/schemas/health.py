"""
Health-check response schema.

Returned by ``GET /health`` to signal service availability.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Standard health-check payload."""

    status: str = Field(default="ok", description="Service health status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the check",
    )
    version: str = Field(default="0.1.0", description="Application version")