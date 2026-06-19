"""
Async application lifecycle manager.

Provides startup and shutdown hooks that are wired into the FastAPI
application via the ``lifespan`` context manager protocol.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Asynchronous lifespan context manager for the FastAPI application.

    Usage in ``main.py``::

        app = FastAPI(lifespan=lifespan)

    Yields control to the application after startup tasks complete.
    Shutdown tasks run when the application server is shutting down.
    """
    # ── Startup ──────────────────────────────────────────────────────
    logger.info("Application startup — initializing resources ...")
    # TODO: Register plugin system, connect to databases, initialise caches, etc.

    yield  # Application runs here.

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Application shutdown — cleaning up resources ...")
    # TODO: Gracefully close database connections, release locks, etc.