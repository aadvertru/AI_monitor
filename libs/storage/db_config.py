"""Environment-based database configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class DBConfigError(ValueError):
    """Raised when database configuration is missing or invalid."""


@dataclass(frozen=True)
class DBConfig:
    database_url: str
    connect_timeout_seconds: float = 5.0


def load_db_config(env: Mapping[str, str] | None = None) -> DBConfig:
    """Load database settings from environment variables."""
    source = env if env is not None else os.environ
    raw_database_url = source.get("DATABASE_URL", "").strip()

    if not raw_database_url:
        raise DBConfigError("DATABASE_URL is required.")

    if not (
        raw_database_url.startswith("postgresql://")
        or raw_database_url.startswith("postgres://")
    ):
        raise DBConfigError("DATABASE_URL must use a Postgres DSN scheme.")

    raw_timeout = source.get("DB_CONNECT_TIMEOUT_SECONDS", "5").strip()
    try:
        timeout_seconds = float(raw_timeout)
    except ValueError as exc:
        raise DBConfigError(
            "DB_CONNECT_TIMEOUT_SECONDS must be a numeric value."
        ) from exc

    if timeout_seconds <= 0:
        raise DBConfigError("DB_CONNECT_TIMEOUT_SECONDS must be greater than 0.")

    return DBConfig(
        database_url=raw_database_url,
        connect_timeout_seconds=timeout_seconds,
    )

