from __future__ import annotations

import unittest

from apps.api.audit_schemas import (
    AnswerMatrixCellResponse,
    AnswerMatrixResponse,
    AuditSummaryV2Response,
    SourceDomainsResponse,
)
from tests.results_v2_fixtures import (
    CONCEPT_COMPETITOR_FIXTURES,
    RESULTS_V2_FIXTURES,
    SOURCE_INTELLIGENCE_V2_FIXTURES,
)


class ResultsV2ContractFixtureTests(unittest.TestCase):
    def test_required_results_v2_fixture_cases_exist(self) -> None:
        self.assertEqual(
            set(RESULTS_V2_FIXTURES),
            {
                "empty_audit",
                "single_model_l1",
                "single_model_l1_l2",
                "multi_model",
                "partial_with_failed_cells",
                "openrouter_gateway_l1_l2",
                "legacy_without_targets",
                "evaluation_null",
            },
        )

    def test_results_v2_fixtures_validate_against_backend_dtos(self) -> None:
        for name, fixture in RESULTS_V2_FIXTURES.items():
            with self.subTest(name=name):
                summary = AuditSummaryV2Response.model_validate(fixture["summary"])
                matrix = AnswerMatrixResponse.model_validate(fixture["matrix"])
                source_domains = SourceDomainsResponse.model_validate(
                    fixture["source_domains"]
                )

                self.assertEqual(summary.concepts, [])
                self.assertEqual(summary.competitor_candidates, [])
                self.assertEqual(source_domains.domains, [])
                self.assertEqual(source_domains.warnings, [])
                for row in matrix.rows:
                    for cell in row.cells:
                        self.assertIsNone(cell.evaluation)
                        self.assertEqual(cell.concepts, [])
                        self.assertEqual(cell.competitor_candidates, [])

    def test_gateway_partial_legacy_and_evaluation_null_contracts_are_stable(
        self,
    ) -> None:
        gateway = AnswerMatrixResponse.model_validate(
            RESULTS_V2_FIXTURES["openrouter_gateway_l1_l2"]["matrix"]
        )
        self.assertEqual([column.level for column in gateway.columns], ["L1", "L2"])
        self.assertEqual([column.gateway for column in gateway.columns], [True, True])
        self.assertEqual(
            [column.gateway_l2_experimental for column in gateway.columns],
            [False, True],
        )

        partial = AnswerMatrixResponse.model_validate(
            RESULTS_V2_FIXTURES["partial_with_failed_cells"]["matrix"]
        )
        failed_cells = [
            cell
            for row in partial.rows
            for cell in row.cells
            if cell.status == "failed"
        ]
        self.assertEqual(failed_cells[0].provider_error.code, "RATE_LIMIT")

        legacy = AnswerMatrixResponse.model_validate(
            RESULTS_V2_FIXTURES["legacy_without_targets"]["matrix"]
        )
        self.assertEqual(legacy.columns[0].target_id, "legacy:mock:L1")
        self.assertFalse(legacy.columns[0].gateway)

        evaluation_null = AnswerMatrixResponse.model_validate(
            RESULTS_V2_FIXTURES["evaluation_null"]["matrix"]
        )
        self.assertIsNone(evaluation_null.rows[0].cells[0].evaluation)

    def test_results_v2_fixtures_do_not_expose_raw_provider_payloads(self) -> None:
        serialized = str(RESULTS_V2_FIXTURES)

        for forbidden in [
            "raw_answer",
            "request_snapshot",
            "raw_prompt",
            "headers",
            "authorization",
            "api_key",
            "sk-",
            "traceback",
        ]:
            self.assertNotIn(forbidden, serialized)

    def test_concepts_competitors_fixture_cases_exist(self) -> None:
        self.assertEqual(
            set(CONCEPT_COMPETITOR_FIXTURES),
            {
                "concepts_only",
                "competitor_candidates_only",
                "concepts_and_competitors",
                "empty_concepts_competitors",
                "generic_phrases_not_competitors",
                "russian_comparison_context",
                "multi_model_evidence",
            },
        )

    def test_concepts_competitors_fixtures_validate_against_backend_dtos(self) -> None:
        for name, fixture in CONCEPT_COMPETITOR_FIXTURES.items():
            with self.subTest(name=name):
                summary = AuditSummaryV2Response.model_validate(fixture["summary"])
                cell = AnswerMatrixCellResponse.model_validate(fixture["matrix_cell"])

                for concept in [*summary.concepts, *cell.concepts]:
                    self.assertEqual(concept.type, "concept")
                    self.assertGreaterEqual(concept.count, 0)
                    self.assertGreaterEqual(concept.evidence_count, 0)

                for candidate in [
                    *summary.competitor_candidates,
                    *cell.competitor_candidates,
                ]:
                    if candidate.confidence is not None:
                        self.assertGreaterEqual(candidate.confidence, 0)
                        self.assertLessEqual(candidate.confidence, 1)
                    self.assertGreaterEqual(candidate.evidence_count, 0)

    def test_generic_legacy_phrases_are_not_competitor_candidates(self) -> None:
        generic = CONCEPT_COMPETITOR_FIXTURES["generic_phrases_not_competitors"]
        summary = AuditSummaryV2Response.model_validate(generic["summary"])
        cell = AnswerMatrixCellResponse.model_validate(generic["matrix_cell"])

        self.assertEqual(summary.competitor_candidates, [])
        self.assertEqual(cell.competitor_candidates, [])
        self.assertEqual(summary.concepts[0].text, "children's ballet classes")

    def test_concepts_competitors_fixtures_do_not_expose_raw_payloads(self) -> None:
        serialized = str(CONCEPT_COMPETITOR_FIXTURES)

        for forbidden in [
            "raw_answer",
            "request_snapshot",
            "raw_prompt",
            "raw_response",
            "headers",
            "authorization",
            "api_key",
            "sk-",
            "traceback",
        ]:
            self.assertNotIn(forbidden, serialized)

    def test_source_intelligence_v2_fixture_cases_exist(self) -> None:
        self.assertEqual(
            set(SOURCE_INTELLIGENCE_V2_FIXTURES),
            {
                "no_sources",
                "single_domain_one_url",
                "single_domain_multiple_urls",
                "same_registrable_domain_across_subdomains",
                "multiple_domains",
                "duplicate_urls",
                "invalid_url_skipped",
                "openrouter_l2_with_citations",
                "openrouter_l2_without_citations",
                "legacy_source_records",
                "partial_audit_some_sources",
            },
        )

    def test_source_intelligence_v2_fixtures_validate_and_preserve_evidence(
        self,
    ) -> None:
        for name, fixture in SOURCE_INTELLIGENCE_V2_FIXTURES.items():
            with self.subTest(name=name):
                response = SourceDomainsResponse.model_validate(fixture)
                for domain in response.domains:
                    self.assertGreaterEqual(domain.source_count, domain.unique_url_count)
                    self.assertGreaterEqual(domain.unique_url_count, len(domain.urls))
                    for url in domain.urls:
                        self.assertTrue(url.normalized_url.startswith(("http://", "https://")))
                        self.assertIsNotNone(url.url)

    def test_source_intelligence_v2_fixtures_do_not_expose_raw_payloads(self) -> None:
        serialized = str(SOURCE_INTELLIGENCE_V2_FIXTURES)

        for forbidden in [
            "raw_answer",
            "request_snapshot",
            "raw_prompt",
            "raw_response",
            "raw_annotations",
            "headers",
            "authorization",
            "api_key",
            "sk-",
            "traceback",
        ]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
