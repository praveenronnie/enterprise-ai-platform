# Health check endpoint
from __future__ import annotations

from fastapi import APIRouter

from backend.app.shared.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status, current timestamp, and version.",
    tags=["system"],
)
async def get_health() -> HealthResponse:
    return HealthResponse()