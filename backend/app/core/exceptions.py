"""
Global exception handlers and custom exception classes.

Maps application-level exceptions to appropriate HTTP responses and
provides a fallback handler for unhandled errors.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings

logger = logging.getLogger(__name__)


# ── Custom Exceptions ────────────────────────────────────────────────


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str = "An application error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class ValidationError(AppException):
    """Raised when input validation fails at the application level."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message=message, status_code=422)


# ── Handlers ─────────────────────────────────────────────────────────


def _build_error_response(status_code: int, message: str, detail: str | None = None) -> JSONResponse:
    """Construct a standardised JSON error response."""
    body: dict[str, object] = {
        "error": {
            "code": status_code,
            "message": message,
        }
    }
    if detail:
        body["error"]["detail"] = detail  # type: ignore[assignment]
    return JSONResponse(status_code=status_code, content=body)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-level exceptions."""
    logger.warning("AppException: %s — %s", exc.status_code, exc.message)
    return _build_error_response(exc.status_code, exc.message)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for any unhandled exception."""
    logger.error("Unhandled exception: %s", traceback.format_exc())
    message = "Internal server error"
    if settings.DEBUG:
        message = str(exc)
    return _build_error_response(500, message)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Wire up all exception handlers to the FastAPI application.

    Should be called during application initialisation.
    """
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]