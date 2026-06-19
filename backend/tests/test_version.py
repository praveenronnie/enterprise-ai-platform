"""Tests for the version-info endpoint."""

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
async def test_version_endpoint(client: AsyncClient) -> None:
    """Verify GET /api/v1/version returns 200 with expected fields."""
    response = await client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert len(data["name"]) > 0
    assert len(data["version"]) > 0