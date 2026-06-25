"""Async database session factory backed by EnvironmentLoader."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.platform.config.loader import EnvironmentLoader
from backend.app.platform.models.document import Base

logger = logging.getLogger(__name__)


def _build_db_url(raw: dict[str, Any]) -> str:
    host = raw.get("DB_HOST", "localhost")
    port = raw.get("DB_PORT", "5432")
    name = raw.get("DB_NAME", "document-engine")
    user = raw.get("DB_USERNAME", "postgres")
    password = raw.get("DB_PASSWORD", "")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


_engine: Any = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_db(env: dict[str, Any] | None = None) -> None:
    """Initialise the async engine and session maker.

    Must be called once at startup.
    """
    global _engine, _async_session_maker  # noqa: PLW0603

    if _engine is not None:
        return

    if env is None:
        env = EnvironmentLoader().load()

    db_url = _build_db_url(env)
    pool_size = int(env.get("DB_POOL_SIZE", 10))
    max_overflow = int(env.get("DB_MAX_OVERFLOW", 5))
    echo = env.get("DB_ECHO", "false").lower() == "true"

    _engine = create_async_engine(
        db_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
        pool_pre_ping=True,
    )
    _async_session_maker = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    logger.info("Async database engine created (pool_size=%d).", pool_size)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    if _async_session_maker is None:
        init_db()
    async with _async_session_maker() as session:  # type: ignore[union-attr]
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables defined in the Base metadata.

    Called during application startup (idempotent).
    """
    if _engine is None:
        init_db()
    async with _engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


async def close_db() -> None:
    """Dispose of the engine on shutdown."""
    global _engine, _async_session_maker  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database engine disposed.")
