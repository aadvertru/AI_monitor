from __future__ import annotations

import unittest

from libs.analysis.source_intelligence import (
    SourceEvidence,
    aggregate_source_domains,
)


class SourceDomainAggregationTests(unittest.TestCase):
    def test_groups_same_registrable_domain_and_preserves_url_evidence(self) -> None:
        result = aggregate_source_domains(
            [
                SourceEvidence(
                    url="https://news.bbc.co.uk/story?a=1&utm_source=x",
                    title="BBC story",
                    snippet="Evidence text",
                    query_id="q1",
                    query_text="news query",
                    target_id="t1",
                    model_id="openrouter/google/gemini",
                    model_provider="google",
                    execution_provider="openrouter",
                    level="L2",
                    source_type="web",
                    gateway=True,
                    gateway_l2_experimental=True,
                ),
                SourceEvidence(
                    url="https://www.bbc.co.uk/other",
                    query_id="q2",
                    target_id="t2",
                    model_id="openrouter/google/gemini",
                    execution_provider="openrouter",
                    level="L2",
                    source_type="web",
                ),
            ]
        )

        self.assertEqual(result.warnings, [])
        self.assertEqual(len(result.domains), 1)
        group = result.domains[0]
        self.assertEqual(group.domain, "bbc.co.uk")
        self.assertEqual(group.source_count, 2)
        self.assertEqual(group.unique_url_count, 2)
        self.assertEqual(group.query_count, 2)
        self.assertEqual(group.target_count, 2)
        self.assertEqual(group.levels, ["L2"])
        self.assertEqual(group.models, ["openrouter/google/gemini"])
        self.assertEqual(group.providers, ["openrouter"])
        self.assertEqual(group.urls[0].title, "BBC story")
        self.assertEqual(group.urls[0].snippet, "Evidence text")
        self.assertTrue(group.urls[0].gateway)

    def test_duplicate_urls_are_counted_as_sources_but_deduplicated(self) -> None:
        result = aggregate_source_domains(
            [
                SourceEvidence(url="https://example.com/page?utm_campaign=x", query_id="q1"),
                SourceEvidence(url="https://EXAMPLE.com:443/page", query_id="q2"),
            ]
        )

        group = result.domains[0]
        self.assertEqual(group.source_count, 2)
        self.assertEqual(group.unique_url_count, 1)
        self.assertEqual(group.query_count, 2)
        self.assertEqual(group.urls[0].normalized_url, "https://example.com/page")

    def test_multiple_domains_sort_by_source_count(self) -> None:
        result = aggregate_source_domains(
            [
                SourceEvidence(url="https://b.example.com/1"),
                SourceEvidence(url="https://a.example.com/2"),
                SourceEvidence(url="https://wikipedia.org/wiki/X"),
            ]
        )

        self.assertEqual(
            [group.domain for group in result.domains],
            ["example.com", "wikipedia.org"],
        )

    def test_invalid_urls_are_skipped_with_warning(self) -> None:
        result = aggregate_source_domains(
            [
                SourceEvidence(url="javascript:alert(1)", title="Unsafe"),
                SourceEvidence(url=None),
                SourceEvidence(url="https://safe.example/path", title="Safe"),
            ]
        )

        self.assertEqual(len(result.domains), 1)
        self.assertEqual(result.domains[0].domain, "safe.example")
        self.assertEqual(result.warnings, ["Skipped 2 invalid source URL(s)."])
        serialized = str(result)
        self.assertNotIn("javascript", serialized)
        self.assertNotIn("Unsafe", serialized)

    def test_no_sources_returns_empty_result(self) -> None:
        result = aggregate_source_domains([])

        self.assertEqual(result.domains, [])
        self.assertEqual(result.warnings, [])


if __name__ == "__main__":
    unittest.main()
