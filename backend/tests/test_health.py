"""Tests for the health-check endpoint."""

from __future__ import annotations

from httpx import AsyncClient, ASGITransport
import pytest

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create an async test client for the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Verify GET /api/v1/health returns 200 with expected fields."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data