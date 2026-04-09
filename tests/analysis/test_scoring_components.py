from __future__ import annotations

import unittest

from libs.analysis.scoring import compute_component_metrics


class ScoringComponentTests(unittest.TestCase):
    def test_brand_detected_happy_path_metrics(self) -> None:
        parsed = {
            "visible_brand": True,
            "prominence_score": 0.6,
            "sentiment": 0.2,
            "recommendation_score": 0.8,
            "source_quality_score": 0.5,
        }

        result = compute_component_metrics(parsed)

        self.assertEqual(result["visibility_score"], 1.0)
        self.assertEqual(result["prominence_score"], 0.6)
        self.assertEqual(result["sentiment_score"], 0.6)
        self.assertEqual(result["recommendation_score"], 0.8)
        self.assertEqual(result["source_quality_score"], 0.5)

    def test_sentiment_normalization_boundaries(self) -> None:
        base = {
            "visible_brand": False,
            "prominence_score": 0.0,
            "recommendation_score": 0.0,
            "source_quality_score": 0.0,
        }

        negative = compute_component_metrics({**base, "sentiment": -1.0})
        neutral = compute_component_metrics({**base, "sentiment": 0.0})
        positive = compute_component_metrics({**base, "sentiment": 1.0})

        self.assertEqual(negative["sentiment_score"], 0.0)
        self.assertEqual(neutral["sentiment_score"], 0.5)
        self.assertEqual(positive["sentiment_score"], 1.0)

    def test_visibility_is_zero_when_brand_not_detected(self) -> None:
        parsed = {
            "visible_brand": False,
            "prominence_score": 0.7,
            "sentiment": 0.4,
            "recommendation_score": 0.9,
            "source_quality_score": 0.2,
        }

        result = compute_component_metrics(parsed)
        self.assertEqual(result["visibility_score"], 0.0)

    def test_out_of_range_values_are_clamped(self) -> None:
        parsed = {
            "visible_brand": True,
            "prominence_score": 5.0,
            "sentiment": -3.0,
            "recommendation_score": -10.0,
            "source_quality_score": 2.0,
        }

        result = compute_component_metrics(parsed)

        self.assertEqual(result["visibility_score"], 1.0)
        self.assertEqual(result["prominence_score"], 1.0)
        self.assertEqual(result["sentiment_score"], 0.0)
        self.assertEqual(result["recommendation_score"], 0.0)
        self.assertEqual(result["source_quality_score"], 1.0)

    def test_missing_fields_use_safe_defaults(self) -> None:
        result = compute_component_metrics({})
        self.assertEqual(
            result,
            {
                "visibility_score": 0.0,
                "prominence_score": 0.0,
                "sentiment_score": 0.0,
                "recommendation_score": 0.0,
                "source_quality_score": 0.0,
            },
        )

    def test_boundary_values_are_handled_correctly(self) -> None:
        parsed = {
            "visible_brand": True,
            "prominence_score": 1.0,
            "sentiment": -1.0,
            "recommendation_score": 0.0,
            "source_quality_score": 1.0,
        }

        result = compute_component_metrics(parsed)

        self.assertEqual(result["visibility_score"], 1.0)
        self.assertEqual(result["prominence_score"], 1.0)
        self.assertEqual(result["sentiment_score"], 0.0)
        self.assertEqual(result["recommendation_score"], 0.0)
        self.assertEqual(result["source_quality_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
