"""Minimal Postgres connectivity helpers for the storage layer."""

from __future__ import annotations

import asyncpg

from .db_config import DBConfig, load_db_config


class DBConnectionError(ConnectionError):
    """Raised when Postgres connection or health check fails."""


async def create_db_connection(config: DBConfig | None = None) -> asyncpg.Connection:
    """Create a database connection using the provided or environment config."""
    resolved_config = config or load_db_config()

    try:
        return await asyncpg.connect(
            dsn=resolved_config.database_url,
            timeout=resolved_config.connect_timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - deterministic wrap for callers.
        raise DBConnectionError("Failed to connect to Postgres.") from exc


async def check_db_connectivity(config: DBConfig | None = None) -> bool:
    """Run a minimal DB health check query (`SELECT 1`)."""
    connection = await create_db_connection(config=config)

    try:
        result = await connection.fetchval("SELECT 1")
        return result == 1
    except Exception as exc:
        raise DBConnectionError("DB connectivity check failed.") from exc
    finally:
        await connection.close()

