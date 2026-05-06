from __future__ import annotations

import unittest

from libs.analysis.competitor_extraction import (
    CompetitorExtractionInput,
    extract_competitor_candidates,
)


class CompetitorExtractionTests(unittest.TestCase):
    def test_english_alternative_context_extracts_brand_like_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="alternatives to HubSpot",
                answer_text="Salesforce and Pipedrive are common alternatives.",
                brand_name="HubSpot",
                query_id=1,
                run_id=2,
                target_id=3,
                level="L1",
                model_id="openai/gpt-4o-mini",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Pipedrive", "Salesforce"])
        self.assertEqual(candidates[0].confidence, 0.7)
        self.assertEqual(candidates[0].evidence_type, "comparison")
        self.assertEqual(candidates[0].evidence[0].query_id, 1)
        self.assertEqual(candidates[0].evidence[0].level, "L1")

    def test_english_vs_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="Oracle vs Snowflake",
                answer_text="Oracle and Snowflake solve overlapping analytics needs.",
                brand_name="Oracle",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Snowflake"])

    def test_english_competitors_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="competitors of HubSpot",
                answer_text="Salesforce is frequently compared with HubSpot.",
                brand_name="HubSpot",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Salesforce"])

    def test_english_similar_tools_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="similar tools to Notion",
                answer_text="Coda and Airtable are similar tools for teams.",
                brand_name="Notion",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Airtable", "Coda"])

    def test_english_top_context_extracts_domain_backed_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="top crm platforms",
                answer_text="Top CRM platforms include salesforce.com and hubspot.com.",
                brand_name="HubSpot",
                brand_domain="hubspot.com",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Salesforce"])

    def test_russian_alternatives_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="альтернативы Nike",
                answer_text="Adidas часто рассматривают как альтернативу Nike.",
                brand_name="Nike",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Adidas"])
        self.assertEqual(candidates[0].evidence[0].language, "ru")

    def test_russian_competitors_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="конкуренты Apple",
                answer_text="Samsung является заметным конкурентом Apple.",
                brand_name="Apple",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Samsung"])

    def test_russian_similar_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="похожие сервисы Notion",
                answer_text="Coda часто называют похожим сервисом.",
                brand_name="Notion",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Coda"])

    def test_russian_top_context_extracts_domain_backed_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="топ CRM платформ",
                answer_text="В топ CRM платформ часто включают salesforce.com и hubspot.com.",
                brand_name="HubSpot",
                brand_domain="hubspot.com",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Salesforce"])

    def test_russian_against_context_extracts_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="Samsung против Apple",
                answer_text="Samsung часто сравнивают против Apple в обзорах смартфонов.",
                brand_name="Apple",
            )
        )

        self.assertEqual([candidate.name for candidate in candidates], ["Samsung"])

    def test_known_competitor_list_match_gets_higher_confidence(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="competitors of Slack",
                answer_text="Microsoft Teams and Discord can be considered alternatives.",
                brand_name="Slack",
                known_competitors=("Microsoft Teams",),
            )
        )

        self.assertEqual(candidates[0].name, "Microsoft Teams")
        self.assertEqual(candidates[0].confidence, 0.9)

    def test_domain_signal_extracts_candidate_with_domain(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="alternatives to Intercom",
                answer_text="Some teams compare Intercom with zendesk.com.",
                brand_name="Intercom",
            )
        )

        self.assertEqual(candidates[0].name, "Zendesk")
        self.assertEqual(candidates[0].domain, "zendesk.com")
        self.assertEqual(candidates[0].confidence, 0.8)

    def test_generic_phrase_not_extracted(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="alternatives to Acme",
                answer_text="dance studio and ballet classes are related concepts.",
                brand_name="Acme",
            )
        )

        self.assertEqual(candidates, [])

    def test_concept_phrase_not_extracted_as_competitor(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="similar tools for brand monitoring",
                answer_text="brand visibility and answer monitoring are useful concepts.",
                brand_name="Acme",
            )
        )

        self.assertEqual(candidates, [])

    def test_confidence_threshold_filters_weak_category_list_candidates(self) -> None:
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="best crm software",
                answer_text="Salesforce and Pipedrive are often listed.",
                brand_name="HubSpot",
            )
        )

        self.assertEqual(candidates, [])

    def test_evidence_does_not_store_full_raw_response(self) -> None:
        long_answer = (
            "Alternatives to Asana include Monday and ClickUp. "
            + "raw-response-tail " * 40
        )
        candidates = extract_competitor_candidates(
            CompetitorExtractionInput(
                query_text="alternatives to Asana",
                answer_text=long_answer,
                brand_name="Asana",
                run_id=10,
                model_id="anthropic/claude-sonnet-4",
            )
        )

        evidence = candidates[0].evidence[0]
        self.assertLessEqual(len(evidence.answer_excerpt), 240)
        self.assertNotEqual(evidence.answer_excerpt, long_answer)
        self.assertEqual(evidence.run_id, 10)
        self.assertEqual(evidence.model_id, "anthropic/claude-sonnet-4")


if __name__ == "__main__":
    unittest.main()
