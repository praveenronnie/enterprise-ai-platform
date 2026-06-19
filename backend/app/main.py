"""
FastAPI application factory and entry point.

Usage::

    # Run with uvicorn (development)
    uvicorn app.main:app --reload

    # Run via prepared script
    python run.py
"""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.version import router as version_router
from app.config.settings import settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.middleware.cors import setup_cors

# ── Initialise logging before anything else ──────────────────────────
setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Application factory.

    Builds and returns a fully configured FastAPI instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI Document Intelligence Platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ── Middleware ───────────────────────────────────────────────────
    setup_cors(app)

    # ── Exception handlers ───────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────
    app.include_router(health_router, prefix="/api/v1", tags=["system"])
    app.include_router(version_router, prefix="/api/v1", tags=["system"])

    logger.info(
        "Application '%s' v%s initialised (debug=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DEBUG,
    )
    return app


# Module-level application instance for ASGI servers (uvicorn, gunicorn, etc.)
app: FastAPI = create_app()


# ── CLI entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )