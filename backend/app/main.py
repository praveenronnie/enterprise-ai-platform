# FastAPI application entry point
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.app.platform.api.v1.ai import router as ai_router
from backend.app.platform.api.v1.document import router as document_router
from backend.app.platform.api.v1.health import router as health_router
from backend.app.platform.api.v1.version import router as version_router
from backend.app.platform.config import ConfigurationManager, EnvironmentLoader
from backend.app.platform.config.settings import Settings
from backend.app.platform.core.exceptions import register_exception_handlers
from backend.app.platform.core.lifespan import lifespan
from backend.app.platform.core.logging import setup_logging
from backend.app.platform.dependencies.container import (
    SERVICE_SETTINGS,
    container,
    register_ai_services,
)
from backend.app.platform.middleware.cors import setup_cors

_loader = EnvironmentLoader()
_raw_config = _loader.load()
_config_manager = ConfigurationManager(_raw_config)
_settings: Settings = _config_manager.build()
container.register(SERVICE_SETTINGS, _settings)
register_ai_services(_settings)

setup_logging()
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = _settings

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI Document Intelligence Platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    setup_cors(app, settings)

    register_exception_handlers(app, settings)

    PREFIX = settings.API_PREFIX

    app.include_router(ai_router, prefix=PREFIX, tags=["ai"])
    app.include_router(document_router, prefix=PREFIX, tags=["documents"])
    app.include_router(health_router, prefix=PREFIX, tags=["system"])
    app.include_router(version_router, prefix=PREFIX, tags=["system"])

    logger.info(
        "Application '%s' v%s initialised (debug=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DEBUG,
    )
    return app


app: FastAPI = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=_settings.HOST,
        port=_settings.PORT,
        reload=_settings.DEBUG,
        log_level=_settings.LOG_LEVEL.lower(),
    )
