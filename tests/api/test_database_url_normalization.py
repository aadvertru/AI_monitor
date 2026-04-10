from __future__ import annotations

import unittest

from apps.api.database import normalize_sqlalchemy_url


class DatabaseURLNormalizationTests(unittest.TestCase):
    def test_sqlite_relative_path_is_normalized_to_aiosqlite(self) -> None:
        self.assertEqual(
            normalize_sqlalchemy_url("sqlite:///./ai_monitor.db"),
            "sqlite+aiosqlite:///./ai_monitor.db",
        )

    def test_sqlite_unix_absolute_path_keeps_four_slashes(self) -> None:
        self.assertEqual(
            normalize_sqlalchemy_url("sqlite:////absolute/path/ai_monitor.db"),
            "sqlite+aiosqlite:////absolute/path/ai_monitor.db",
        )

    def test_existing_aiosqlite_url_is_preserved(self) -> None:
        self.assertEqual(
            normalize_sqlalchemy_url("sqlite+aiosqlite:///./ai_monitor.db"),
            "sqlite+aiosqlite:///./ai_monitor.db",
        )


if __name__ == "__main__":
    unittest.main()
