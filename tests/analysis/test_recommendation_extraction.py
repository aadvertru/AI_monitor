from __future__ import annotations

import unittest

from libs.analysis.preprocessing import PreprocessedText, preprocess
from libs.analysis.recommendation_extraction import extract_recommendation


class RecommendationExtractionTests(unittest.TestCase):
    def test_best_returns_strongest_score(self) -> None:
        preprocessed = preprocess("This is the best platform for teams.")
        self.assertEqual(extract_recommendation(preprocessed), 1.0)

    def test_recommended_returns_medium_high_score(self) -> None:
        preprocessed = preprocess("This option is recommended for startups.")
        self.assertEqual(extract_recommendation(preprocessed), 0.8)

    def test_listed_returns_low_score(self) -> None:
        preprocessed = preprocess("Acme was listed among many tools.")
        self.assertEqual(extract_recommendation(preprocessed), 0.3)

    def test_multiple_patterns_return_highest_weight(self) -> None:
        preprocessed = preprocess("It is listed and also a top choice.")
        self.assertEqual(extract_recommendation(preprocessed), 1.0)

    def test_no_recommendation_signal_returns_zero(self) -> None:
        preprocessed = preprocess("This platform has many dashboards and reports.")
        self.assertEqual(extract_recommendation(preprocessed), 0.0)

    def test_empty_or_none_preprocessed_returns_zero(self) -> None:
        empty_preprocessed = PreprocessedText(original="", lowered="", sentences=[])
        self.assertEqual(extract_recommendation(empty_preprocessed), 0.0)
        self.assertEqual(extract_recommendation(None), 0.0)

    def test_substring_does_not_match(self) -> None:
        preprocessed = preprocess("This product was bested by alternatives.")
        self.assertEqual(extract_recommendation(preprocessed), 0.0)


if __name__ == "__main__":
    unittest.main()
