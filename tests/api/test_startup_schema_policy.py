from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from apps.api.database import should_auto_create_schema
from apps.api.main import on_startup


class StartupSchemaPolicyTests(unittest.IsolatedAsyncioTestCase):
    def test_auto_create_schema_disabled_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(should_auto_create_schema())

    def test_auto_create_schema_enabled_for_truthy_values(self) -> None:
        with patch.dict("os.environ", {"AUTO_CREATE_SCHEMA": "true"}, clear=True):
            self.assertTrue(should_auto_create_schema())
        with patch.dict("os.environ", {"AUTO_CREATE_SCHEMA": " 1 "}, clear=True):
            self.assertTrue(should_auto_create_schema())

    def test_auto_create_schema_disabled_for_non_truthy_values(self) -> None:
        with patch.dict("os.environ", {"AUTO_CREATE_SCHEMA": "false"}, clear=True):
            self.assertFalse(should_auto_create_schema())
        with patch.dict("os.environ", {"AUTO_CREATE_SCHEMA": "0"}, clear=True):
            self.assertFalse(should_auto_create_schema())

    async def test_startup_skips_schema_creation_when_disabled(self) -> None:
        with (
            patch("apps.api.main.should_auto_create_schema", return_value=False),
            patch("apps.api.main.init_models", new_callable=AsyncMock) as init_mock,
        ):
            await on_startup()
            init_mock.assert_not_awaited()

    async def test_startup_runs_schema_creation_when_enabled(self) -> None:
        with (
            patch("apps.api.main.should_auto_create_schema", return_value=True),
            patch("apps.api.main.init_models", new_callable=AsyncMock) as init_mock,
        ):
            await on_startup()
            init_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
