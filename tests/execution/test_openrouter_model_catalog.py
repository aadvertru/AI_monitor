from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from typing import Any

from libs.execution.openrouter_model_catalog import (
    CATALOG_REFRESH_FAILED_WARNING,
    ModelCatalogResponse,
    OpenRouterModelCatalogCache,
    OpenRouterModelCatalogConfig,
    OpenRouterModelCatalogService,
    load_openrouter_model_catalog_config,
    normalize_openrouter_catalog,
)


class _FakeCatalogClient:
    def __init__(self, *, raw: Any | None = None, exc: Exception | None = None) -> None:
        self.raw = raw if raw is not None else _raw_catalog()
        self.exc = exc
        self.calls = 0

    async def fetch_user_models(self, config: OpenRouterModelCatalogConfig) -> Any:
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.raw


def _config(**overrides) -> OpenRouterModelCatalogConfig:
    values = {
        "enabled": True,
        "api_key": "sk-hidden",
        "allowed_models": (
            "openai/gpt-4o-mini",
            "google/gemini-2.0-flash-001",
            "anthropic/claude-3.5-sonnet",
        ),
        "cache_ttl_seconds": 86_400,
    }
    values.update(overrides)
    return OpenRouterModelCatalogConfig(**values)


def _raw_catalog() -> dict[str, Any]:
    return {
        "data": [
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o mini",
                "context_length": 128000,
                "pricing": {"prompt": "secret-ish billing data not exposed"},
            },
            {
                "id": "google/gemini-2.0-flash-001",
                "name": "Gemini 2.0 Flash",
            },
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
            },
            {
                "id": "meta-llama/llama-3",
                "name": "Disallowed unknown family",
            },
            {
                "id": "openai/not-allowed",
                "name": "Disallowed OpenAI",
            },
        ],
        "headers": {"authorization": "Bearer sk-hidden"},
    }


class OpenRouterModelCatalogServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_catalog_does_not_call_openrouter(self) -> None:
        client = _FakeCatalogClient()
        service = OpenRouterModelCatalogService(
            config=_config(enabled=False),
            client=client,
        )

        result = await service.get_catalog()

        self.assertEqual(client.calls, 0)
        self.assertEqual(result.families, [])
        self.assertEqual(result.diagnostic["code"], "PROVIDER_DISABLED")

    async def test_missing_api_key_does_not_call_openrouter(self) -> None:
        client = _FakeCatalogClient()
        service = OpenRouterModelCatalogService(
            config=_config(api_key=None),
            client=client,
        )

        result = await service.get_catalog()

        self.assertEqual(client.calls, 0)
        self.assertEqual(result.diagnostic["code"], "NO_API_KEY")

    async def test_missing_allowed_models_returns_configuration_error(self) -> None:
        client = _FakeCatalogClient()
        service = OpenRouterModelCatalogService(
            config=_config(allowed_models=()),
            client=client,
        )

        result = await service.get_catalog()

        self.assertEqual(client.calls, 0)
        self.assertEqual(result.diagnostic["code"], "CONFIGURATION_ERROR")

    async def test_fetch_returns_allowed_only_grouped_frontend_catalog(self) -> None:
        service = OpenRouterModelCatalogService(
            config=_config(),
            client=_FakeCatalogClient(),
            clock=lambda: datetime(2026, 5, 5, tzinfo=UTC),
        )

        result = await service.get_catalog()

        self.assertEqual([family.id for family in result.families], ["chatgpt", "gemini", "claude"])
        models = [model for family in result.families for model in family.models]
        self.assertEqual(
            {model.model_id for model in models},
            {
                "openai/gpt-4o-mini",
                "google/gemini-2.0-flash-001",
                "anthropic/claude-3.5-sonnet",
            },
        )
        self.assertTrue(all(model.execution_provider == "openrouter" for model in models))
        self.assertTrue(all(model.supports_l1 for model in models))
        self.assertTrue(all(model.supports_l2_gateway for model in models))
        self.assertTrue(all(model.l2_experimental for model in models))
        self.assertEqual(result.cached_at, datetime(2026, 5, 5, tzinfo=UTC))
        self.assertEqual(result.expires_at, datetime(2026, 5, 6, tzinfo=UTC))

    async def test_frontend_catalog_does_not_include_is_allowed_or_raw_payload(self) -> None:
        service = OpenRouterModelCatalogService(
            config=_config(),
            client=_FakeCatalogClient(),
        )

        result = await service.get_catalog()
        dumped = result.model_dump_json()

        self.assertNotIn("is_allowed", dumped)
        self.assertNotIn("pricing", dumped)
        self.assertNotIn("authorization", dumped.lower())
        self.assertNotIn("sk-hidden", dumped)

    async def test_cache_hit_avoids_repeated_fetch(self) -> None:
        now = datetime(2026, 5, 5, tzinfo=UTC)
        client = _FakeCatalogClient()
        cache = OpenRouterModelCatalogCache()
        service = OpenRouterModelCatalogService(
            config=_config(),
            client=client,
            cache=cache,
            clock=lambda: now,
        )

        first = await service.get_catalog()
        second = await service.get_catalog()

        self.assertEqual(client.calls, 1)
        self.assertEqual(first.model_dump(), second.model_dump())

    async def test_cache_expires_and_refreshes(self) -> None:
        moments = [
            datetime(2026, 5, 5, tzinfo=UTC),
            datetime(2026, 5, 7, tzinfo=UTC),
        ]
        client = _FakeCatalogClient()
        cache = OpenRouterModelCatalogCache()

        first = await OpenRouterModelCatalogService(
            config=_config(cache_ttl_seconds=60),
            client=client,
            cache=cache,
            clock=lambda: moments[0],
        ).get_catalog()
        second = await OpenRouterModelCatalogService(
            config=_config(cache_ttl_seconds=60),
            client=client,
            cache=cache,
            clock=lambda: moments[1],
        ).get_catalog()

        self.assertEqual(client.calls, 2)
        self.assertNotEqual(first.cached_at, second.cached_at)

    async def test_fetch_failure_with_cache_returns_stale_cache_with_safe_warning(self) -> None:
        now = datetime(2026, 5, 5, tzinfo=UTC)
        cache = OpenRouterModelCatalogCache()
        await OpenRouterModelCatalogService(
            config=_config(cache_ttl_seconds=60),
            client=_FakeCatalogClient(),
            cache=cache,
            clock=lambda: now,
        ).get_catalog()

        stale_result = await OpenRouterModelCatalogService(
            config=_config(cache_ttl_seconds=60),
            client=_FakeCatalogClient(exc=RuntimeError("sk-hidden raw failure")),
            cache=cache,
            clock=lambda: now + timedelta(days=1),
        ).get_catalog()

        self.assertEqual(stale_result.warnings, [CATALOG_REFRESH_FAILED_WARNING])
        self.assertGreater(len(stale_result.families), 0)
        self.assertNotIn("sk-hidden", stale_result.model_dump_json())

    async def test_fetch_failure_without_cache_returns_safe_diagnostic(self) -> None:
        service = OpenRouterModelCatalogService(
            config=_config(),
            client=_FakeCatalogClient(exc=RuntimeError("raw sk-hidden failure")),
        )

        result = await service.get_catalog()

        self.assertEqual(result.families, [])
        self.assertEqual(result.diagnostic["code"], "PROVIDER_REQUEST_FAILED")
        self.assertNotIn("sk-hidden", result.model_dump_json())

    def test_unknown_provider_prefix_is_not_assigned_to_supported_family(self) -> None:
        result = normalize_openrouter_catalog(
            {"data": [{"id": "unknown/model", "name": "Unknown"}]},
            allowed_models={"unknown/model"},
        )

        self.assertEqual(result, [])

    def test_env_config_loader(self) -> None:
        config = load_openrouter_model_catalog_config(
            {
                "OPENROUTER_CATALOG_ENABLED": "false",
                "OPENROUTER_API_KEY": " sk-test ",
                "OPENROUTER_ALLOWED_MODELS": "openai/a, google/b",
                "OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS": "120",
            }
        )

        self.assertFalse(config.enabled)
        self.assertEqual(config.api_key, "sk-test")
        self.assertEqual(config.allowed_models, ("openai/a", "google/b"))
        self.assertEqual(config.cache_ttl_seconds, 120)
        self.assertNotIn("sk-test", repr(config))
        self.assertEqual(config.safe_log_dict()["api_key"], "***")

    def test_response_extra_fields_are_forbidden(self) -> None:
        result = ModelCatalogResponse(families=[])

        with self.assertRaises(ValueError):
            ModelCatalogResponse.model_validate({**result.model_dump(), "is_allowed": True})


if __name__ == "__main__":
    unittest.main()
