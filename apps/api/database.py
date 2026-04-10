"""Async database wiring for API handlers."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from libs.storage.models import Base

DEFAULT_DATABASE_URL = "sqlite:///./ai_monitor.db"
AUTO_CREATE_SCHEMA_ENV = "AUTO_CREATE_SCHEMA"
_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def should_auto_create_schema() -> bool:
    raw_value = os.getenv(AUTO_CREATE_SCHEMA_ENV)
    if raw_value is None:
        return False
    return raw_value.strip().lower() in _TRUE_ENV_VALUES


def normalize_sqlalchemy_url(raw_url: str) -> str:
    """Normalize database URLs to async SQLAlchemy drivers.

    Note: for SQLite URLs, slash semantics are preserved as-is.
    Example: sqlite:////absolute/path.db -> sqlite+aiosqlite:////absolute/path.db
    """
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw_url.startswith("sqlite://") and not raw_url.startswith("sqlite+aiosqlite://"):
        return f"sqlite+aiosqlite://{raw_url[len('sqlite://'):]}"
    return raw_url


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(normalize_sqlalchemy_url(get_database_url()))
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory


async def init_models(engine: AsyncEngine | None = None) -> None:
    """Create tables from metadata for local dev/test environments only."""
    resolved_engine = engine or get_engine()
    async with resolved_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

