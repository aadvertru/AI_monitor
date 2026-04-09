from __future__ import annotations

import unittest

from libs.analysis.parser import parse
from libs.execution.provider_adapter import ProviderResponse

EXPECTED_KEYS = {
    "visible_brand",
    "brand_position_rank",
    "prominence_score",
    "sentiment",
    "recommendation_score",
    "source_quality_score",
    "competitors",
    "sources",
    "parsed_payload",
}

SAFE_DEFAULTS = {
    "visible_brand": False,
    "brand_position_rank": None,
    "prominence_score": 0.0,
    "sentiment": 0.0,
    "recommendation_score": 0.0,
    "source_quality_score": 0.0,
    "competitors": [],
    "sources": [],
    "parsed_payload": {},
}


class ParserTests(unittest.TestCase):
    def test_successful_response_with_brand_mention_returns_full_result(self) -> None:
        provider_response = ProviderResponse(
            status="success",
            raw_answer=(
                "Acme AI is the best option for teams. "
                "Many users recommend Acme AI. "
                "Beta Labs is another vendor."
            ),
            citations=[{"url": "https://www.wikipedia.org/wiki/Acme_AI", "title": "Acme"}],
            response_time=0.25,
            error=None,
            provider_metadata={"model": "mock"},
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain="acme.ai",
            query="best ai tools",
            provider_response=provider_response,
        )

        self.assertEqual(set(result.keys()), EXPECTED_KEYS)
        self.assertTrue(result["visible_brand"])
        self.assertEqual(result["brand_position_rank"], 1)
        self.assertGreater(result["prominence_score"], 0.0)
        self.assertLessEqual(result["prominence_score"], 1.0)
        self.assertEqual(result["sentiment"], 1.0)
        self.assertEqual(result["recommendation_score"], 1.0)
        self.assertEqual(result["source_quality_score"], 0.5)
        self.assertGreaterEqual(len(result["competitors"]), 1)
        self.assertEqual(result["sources"][0]["domain"], "wikipedia.org")
        self.assertEqual(
            result["parsed_payload"],
            {
                "match_type": "exact",
                "mention_count": 2,
                "competitor_count": 1,
            },
        )

    def test_contract_keys_are_exact_no_extra_no_missing(self) -> None:
        provider_response = ProviderResponse(
            status="success",
            raw_answer="Acme AI appears in this answer.",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata=None,
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain=None,
            query="acme ai",
            provider_response=provider_response,
        )

        self.assertEqual(set(result.keys()), EXPECTED_KEYS)

    def test_error_status_returns_safe_defaults(self) -> None:
        provider_response = ProviderResponse(
            status="error",
            raw_answer=None,
            citations=None,
            response_time=0.2,
            error={"code": "provider_error", "message": "failed"},
            provider_metadata=None,
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain="acme.ai",
            query="best ai tools",
            provider_response=provider_response,
        )
        self.assertEqual(result, SAFE_DEFAULTS)

    def test_none_raw_answer_returns_safe_defaults(self) -> None:
        provider_response = ProviderResponse(
            status="success",
            raw_answer=None,
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata=None,
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain="acme.ai",
            query="best ai tools",
            provider_response=provider_response,
        )
        self.assertEqual(result, SAFE_DEFAULTS)

    def test_empty_raw_answer_returns_safe_defaults(self) -> None:
        provider_response = ProviderResponse(
            status="success",
            raw_answer="",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata=None,
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain="acme.ai",
            query="best ai tools",
            provider_response=provider_response,
        )
        self.assertEqual(result, SAFE_DEFAULTS)

    def test_brand_not_found_sets_visible_false_rank_none_prominence_zero(self) -> None:
        provider_response = ProviderResponse(
            status="success",
            raw_answer="This platform provides dashboards and automation.",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata=None,
        )

        result = parse(
            brand_name="Acme AI",
            brand_domain="acme.ai",
            query="best ai tools",
            provider_response=provider_response,
        )

        self.assertFalse(result["visible_brand"])
        self.assertIsNone(result["brand_position_rank"])
        self.assertEqual(result["prominence_score"], 0.0)
        self.assertEqual(set(result.keys()), EXPECTED_KEYS)


if __name__ == "__main__":
    unittest.main()
