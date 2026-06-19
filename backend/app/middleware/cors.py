"""
CORS middleware configuration.

Configures Cross-Origin Resource Sharing based on application settings.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings


def setup_cors(app: FastAPI) -> None:
    """
    Register the CORS middleware on the FastAPI application.

    Call during application initialisation before any routes are added.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )