"""
Version-info endpoint.

Provides metadata about the running application such as name, version,
and description.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import settings
from app.schemas.version import VersionResponse

router = APIRouter()


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Get version info",
    description="Returns application name, version, and description.",
    tags=["system"],
)
async def get_version() -> VersionResponse:
    """Return version metadata from the application settings."""
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )