# Version info endpoint
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.platform.config.settings import Settings
from backend.app.platform.dependencies.container import get_settings
from backend.app.shared.schemas.version import VersionResponse

router = APIRouter()


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Get version info",
    description="Returns application name, version, and description.",
    tags=["system"],
)
async def get_version(
    settings: Settings = Depends(get_settings),
) -> VersionResponse:
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )