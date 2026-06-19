"""
Version-info response schema.

Returned by ``GET /version`` to describe the running build.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    """Version metadata payload."""

    name: str = Field(default="Enterprise AI Platform", description="Application name")
    version: str = Field(default="0.1.0", description="Semantic version string")
    description: str = Field(
        default="Enterprise AI Document Intelligence Platform",
        description="Short description",
    )