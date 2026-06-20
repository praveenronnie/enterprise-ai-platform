# Exception handlers
from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.platform.config.settings import Settings

logger = logging.getLogger(__name__)


class AppException(Exception):

    def __init__(
        self, message: str = "An application error occurred", status_code: int = 500
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class ValidationError(AppException):

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message=message, status_code=422)


def _build_error_response(
    status_code: int, message: str, detail: str | None = None
) -> JSONResponse:
    body: dict[str, object] = {
        "error": {
            "code": status_code,
            "message": message,
        }
    }
    if detail:
        body["error"]["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


def _make_app_exception_handler(settings: Settings):
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        logger.warning("AppException: %s — %s", exc.status_code, exc.message)
        return _build_error_response(exc.status_code, exc.message)

    return app_exception_handler


def _make_unhandled_exception_handler(settings: Settings):
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception: %s", traceback.format_exc())
        message = "Internal server error"
        if settings.DEBUG:
            message = str(exc)
        return _build_error_response(500, message)

    return unhandled_exception_handler


def register_exception_handlers(app: FastAPI, settings: Settings) -> None:
    app.add_exception_handler(AppException, _make_app_exception_handler(settings))
    app.add_exception_handler(Exception, _make_unhandled_exception_handler(settings))
