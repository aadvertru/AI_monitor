from __future__ import annotations

import unittest

from libs.analysis.competitor_extraction import CompetitorCandidate, extract_competitors
from libs.analysis.preprocessing import PreprocessedText, preprocess


class CompetitorExtractionTests(unittest.TestCase):
    def test_multiple_competitors_with_correct_frequencies(self) -> None:
        preprocessed = preprocess(
            "We compared Nova Cloud and Zen Labs. Later Nova Cloud beat Pixel Studio."
        )

        candidates = extract_competitors(preprocessed, brand_name="Acme AI")

        self.assertEqual(
            candidates,
            [
                CompetitorCandidate(name="nova cloud", frequency=2),
                CompetitorCandidate(name="pixel studio", frequency=1),
                CompetitorCandidate(name="zen labs", frequency=1),
            ],
        )

    def test_target_brand_is_excluded(self) -> None:
        preprocessed = preprocess("Acme AI competes with Nova Cloud. ACME AI also appears.")

        candidates = extract_competitors(preprocessed, brand_name="Acme AI")

        self.assertEqual(candidates, [CompetitorCandidate(name="nova cloud", frequency=1)])

    def test_no_competitors_returns_empty_list(self) -> None:
        preprocessed = preprocess("this text has no capitalized brand-like entities")
        self.assertEqual(extract_competitors(preprocessed, brand_name="Acme AI"), [])

    def test_duplicate_mentions_count_frequency(self) -> None:
        preprocessed = preprocess("Nova Cloud integrates with Nova Cloud and Nova Cloud.")

        candidates = extract_competitors(preprocessed, brand_name="Acme AI")

        self.assertEqual(candidates, [CompetitorCandidate(name="nova cloud", frequency=3)])

    def test_empty_preprocessed_text_returns_empty_list(self) -> None:
        preprocessed = PreprocessedText(original="", lowered="", sentences=[])
        self.assertEqual(extract_competitors(preprocessed, brand_name="Acme AI"), [])

    def test_sentence_start_capitalization_is_not_false_positive(self) -> None:
        preprocessed = preprocess("This AI improves reports. Another sentence follows.")

        candidates = extract_competitors(preprocessed, brand_name="Acme AI")

        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()

