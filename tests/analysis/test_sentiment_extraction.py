from __future__ import annotations

import unittest

from libs.analysis.preprocessing import PreprocessedText, preprocess
from libs.analysis.sentiment_extraction import extract_sentiment


class SentimentExtractionTests(unittest.TestCase):
    def test_positive_keywords_return_positive_score(self) -> None:
        preprocessed = preprocess("Acme is a great and reliable platform.")

        score = extract_sentiment(preprocessed)

        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_negative_keywords_return_negative_score(self) -> None:
        preprocessed = preprocess("This tool is bad and unreliable.")

        score = extract_sentiment(preprocessed)

        self.assertLess(score, 0.0)
        self.assertGreaterEqual(score, -1.0)

    def test_neutral_text_returns_zero(self) -> None:
        preprocessed = preprocess("This platform has many features.")
        self.assertEqual(extract_sentiment(preprocessed), 0.0)

    def test_conflicting_keywords_resolve_by_net_count(self) -> None:
        preprocessed = preprocess("Best option but bad and poor support.")
        self.assertAlmostEqual(extract_sentiment(preprocessed), -1.0 / 3.0)

    def test_equal_positive_and_negative_counts_return_zero(self) -> None:
        preprocessed = preprocess("Great interface but bad reliability.")
        self.assertEqual(extract_sentiment(preprocessed), 0.0)

    def test_empty_or_none_preprocessed_returns_zero(self) -> None:
        empty_preprocessed = PreprocessedText(original="", lowered="", sentences=[])
        self.assertEqual(extract_sentiment(empty_preprocessed), 0.0)
        self.assertEqual(extract_sentiment(None), 0.0)

    def test_substring_keyword_does_not_match(self) -> None:
        preprocessed = preprocess("This is the greatest product.")
        self.assertEqual(extract_sentiment(preprocessed), 0.0)


if __name__ == "__main__":
    unittest.main()
