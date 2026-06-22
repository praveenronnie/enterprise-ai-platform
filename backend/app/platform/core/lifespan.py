# Application lifespan
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.app.platform.config.storage import StorageManager
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize storage paths
    StorageManager.initialize()

    logger.info("Application startup — running startup hooks ...")

    yield

    logger.info("Application shutdown — cleaning up resources ...")
