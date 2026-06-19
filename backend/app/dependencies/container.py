"""
Lightweight dependency-injection container.

Provides a central registry for service instances so that FastAPI
route handlers can declare their dependencies via ``Depends()``.

This follows the "Composition Root" pattern — all wiring happens in
one place at application startup.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any

from fastapi import Request

from app.config.settings import settings

logger = logging.getLogger(__name__)


# ── Container ────────────────────────────────────────────────────────


class DIContainer:
    """
    Simple inversion-of-control container.

    Register service instances with ``register()`` then retrieve them
    from FastAPI dependencies with ``resolve()``.
    """

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, key: str, instance: object) -> None:
        """Register a service *instance* under a string *key*."""
        self._services[key] = instance
        logger.debug("Registered service: %s (%s)", key, type(instance).__name__)

    def resolve(self, key: str) -> object:
        if key not in self._services:
            raise KeyError(f"Service '{key}' is not registered")
        return self._services[key]


# Module-level singleton
container: DIContainer = DIContainer()
"""
Pre-initialised DI container.

Populated during the application startup lifecycle hook.
"""


# ── FastAPI dependencies ─────────────────────────────────────────────


def get_container() -> Generator[DIContainer, None, None]:
    """FastAPI dependency that yields the DI container."""
    yield container


async def get_request_id(request: Request) -> str:
    """
    Return a unique identifier for the current request.

    Falls back to ``X-Request-ID`` header or generates a UUID.
    """
    return request.headers.get("X-Request-ID", "")