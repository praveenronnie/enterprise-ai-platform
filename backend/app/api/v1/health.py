"""
Health-check endpoint.

Provides a simple liveness probe for load balancers and orchestration
platforms (Kubernetes, Docker Compose health checks, etc.).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status, current timestamp, and version.",
    tags=["system"],
)
async def get_health() -> HealthResponse:
    """Return a simple health-check payload."""
    return HealthResponse()
