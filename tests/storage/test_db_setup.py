from __future__ import annotations

import unittest
from unittest.mock import patch

from libs.storage.db import check_db_connectivity
from libs.storage.db_config import DBConfig, DBConfigError, load_db_config


class _FakeConnection:
    def __init__(self, fetch_value: int = 1) -> None:
        self.fetch_value = fetch_value
        self.queries: list[str] = []
        self.closed = False

    async def fetchval(self, query: str) -> int:
        self.queries.append(query)
        return self.fetch_value

    async def close(self) -> None:
        self.closed = True


class DBSetupTests(unittest.IsolatedAsyncioTestCase):
    async def test_db_connectivity_runs_select_1_happy_path(self) -> None:
        fake_connection = _FakeConnection(fetch_value=1)

        async def _fake_connect(*, dsn: str, timeout: float) -> _FakeConnection:
            self.assertEqual(dsn, "postgresql://user:pass@localhost:5432/monitor")
            self.assertEqual(timeout, 2.5)
            return fake_connection

        config = DBConfig(
            database_url="postgresql://user:pass@localhost:5432/monitor",
            connect_timeout_seconds=2.5,
        )

        with patch("libs.storage.db.asyncpg.connect", side_effect=_fake_connect):
            is_healthy = await check_db_connectivity(config=config)

        self.assertTrue(is_healthy)
        self.assertEqual(fake_connection.queries, ["SELECT 1"])
        self.assertTrue(fake_connection.closed)

    async def test_missing_database_url_fails_predictably(self) -> None:
        with self.assertRaises(DBConfigError) as context:
            load_db_config(env={})

        self.assertEqual(str(context.exception), "DATABASE_URL is required.")


if __name__ == "__main__":
    unittest.main()

