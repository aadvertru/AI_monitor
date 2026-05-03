from __future__ import annotations

import json
import unittest

from apps.api.services.seed_query_generation import (
    GENERATION_UNAVAILABLE_WARNING,
    GenerateSeedQueriesInput,
    SeedQueryDraft,
    SeedQueryGenerationConfig,
    SeedQueryGenerationConfigError,
    SeedQueryGenerationUnavailable,
    generate_seed_query_suggestions,
)


class SeedQueryGenerationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_provider_json_returns_structured_suggestions(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {
                            "text": "Best SEO agencies in Finland",
                            "type": "category_discovery",
                        }
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name="Seopaja",
                brand_domain="seopaja.fi",
                brand_description="SEO services for small businesses in Finland",
                use_domain=True,
                use_description=True,
                existing_queries=[],
            ),
            provider=provider,
        )

        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0].text, "Best SEO agencies in Finland")
        self.assertEqual(result.suggestions[0].type, "category_discovery")
        self.assertEqual(result.suggestions[0].source, "ai")

    async def test_invalid_json_is_handled_safely(self) -> None:
        async def provider(_prompt: str) -> str:
            return "not json"

        result = await generate_seed_query_suggestions(
            _valid_input(),
            provider=provider,
        )

        self.assertEqual(result.suggestions, [])
        self.assertEqual(result.warnings, [GENERATION_UNAVAILABLE_WARNING])

    async def test_missing_top_level_queries_is_handled_safely(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps({"items": []})

        result = await generate_seed_query_suggestions(
            _valid_input(),
            provider=provider,
        )

        self.assertEqual(result.suggestions, [])
        self.assertEqual(result.warnings, [GENERATION_UNAVAILABLE_WARNING])

    async def test_invalid_provider_items_are_filtered(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {"type": "brand_direct"},
                        {"text": "   ", "type": "brand_direct"},
                        {"text": "Unknown type", "type": "unknown"},
                        {"text": "Valid recommendation", "type": "recommendation"},
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            _valid_input(),
            provider=provider,
        )

        self.assertEqual(
            [suggestion.text for suggestion in result.suggestions],
            ["Valid recommendation"],
        )

    async def test_duplicate_provider_suggestions_are_deduplicated(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {"text": "Compare Acme tools", "type": "comparison"},
                        {"text": "  compare   acme tools  ", "type": "comparison"},
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            _valid_input(),
            provider=provider,
        )

        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.skipped_duplicates, 1)

    async def test_duplicate_against_existing_queries_is_skipped(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {"text": "What is Seopaja?", "type": "brand_direct"},
                        {"text": "Best SEO agencies", "type": "category_discovery"},
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name="Seopaja",
                brand_description="SEO services",
                use_description=True,
                existing_queries=[SeedQueryDraft(text="what is seopaja?")],
            ),
            provider=provider,
        )

        self.assertEqual(
            [suggestion.text for suggestion in result.suggestions],
            ["Best SEO agencies"],
        )
        self.assertEqual(result.skipped_duplicates, 1)

    async def test_existing_query_count_limits_returned_suggestions(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {"text": "Unique query one", "type": "recommendation"},
                        {"text": "Unique query two", "type": "comparison"},
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name="Acme",
                brand_description="A useful service",
                use_description=True,
                existing_queries=[
                    SeedQueryDraft(text=f"existing query {index}") for index in range(19)
                ],
            ),
            provider=provider,
        )

        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.skipped_limit, 1)

    async def test_existing_query_count_at_limit_returns_warning_without_provider_call(
        self,
    ) -> None:
        async def provider(_prompt: str) -> str:
            raise AssertionError("provider should not be called")

        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name="Acme",
                brand_description="A useful service",
                use_description=True,
                existing_queries=[
                    SeedQueryDraft(text=f"existing query {index}") for index in range(20)
                ],
            ),
            provider=provider,
        )

        self.assertEqual(result.suggestions, [])
        self.assertEqual(result.skipped_limit, 10)
        self.assertEqual(result.warnings, ["Seed query limit is already reached."])

    async def test_provider_error_is_handled_safely(self) -> None:
        async def provider(_prompt: str) -> str:
            raise TimeoutError("provider timed out with hidden details")

        result = await generate_seed_query_suggestions(
            _valid_input(),
            provider=provider,
        )

        self.assertEqual(result.suggestions, [])
        self.assertEqual(result.warnings, [GENERATION_UNAVAILABLE_WARNING])

    async def test_count_ten_is_accepted(self) -> None:
        async def provider(_prompt: str) -> str:
            return json.dumps(
                {
                    "queries": [
                        {"text": f"Generated query {index}", "type": "recommendation"}
                        for index in range(10)
                    ]
                }
            )

        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name="Seopaja",
                brand_description="SEO services",
                use_description=True,
                count=10,
                existing_queries=[],
            ),
            provider=provider,
        )

        self.assertEqual(len(result.suggestions), 10)

    async def test_mock_provider_requires_explicit_enabled_mock_config(self) -> None:
        result = await generate_seed_query_suggestions(
            _valid_input(),
            config=SeedQueryGenerationConfig(enabled=True, provider="mock"),
        )

        self.assertEqual(len(result.suggestions), 10)

    async def test_disabled_generation_raises_safe_unavailable_error(self) -> None:
        with self.assertRaises(SeedQueryGenerationUnavailable):
            await generate_seed_query_suggestions(
                _valid_input(),
                config=SeedQueryGenerationConfig(enabled=False, provider="mock"),
            )

    async def test_openai_mode_without_api_key_raises_safe_unavailable_error(self) -> None:
        with self.assertRaises(SeedQueryGenerationUnavailable):
            await generate_seed_query_suggestions(
                _valid_input(),
                config=SeedQueryGenerationConfig(enabled=True, provider="openai"),
            )

    async def test_input_validation_rejects_invalid_generation_requests(self) -> None:
        invalid_inputs = [
            GenerateSeedQueriesInput(use_domain=False, use_description=False),
            GenerateSeedQueriesInput(use_domain=True, brand_domain=None),
            GenerateSeedQueriesInput(use_domain=True, brand_domain="https://bad.example"),
            GenerateSeedQueriesInput(use_description=True, brand_description=" "),
            GenerateSeedQueriesInput(use_description=True, brand_description="ok", count=11),
        ]

        for payload in invalid_inputs:
            with self.subTest(payload=payload), self.assertRaises(
                SeedQueryGenerationConfigError
            ):
                await generate_seed_query_suggestions(
                    payload,
                    provider=lambda _prompt: _async_json({"queries": []}),
                )


def _valid_input() -> GenerateSeedQueriesInput:
    return GenerateSeedQueriesInput(
        brand_name="Seopaja",
        brand_description="SEO services for small businesses in Finland",
        use_description=True,
        existing_queries=[],
    )


async def _async_json(value: object) -> str:
    return json.dumps(value)


if __name__ == "__main__":
    unittest.main()
