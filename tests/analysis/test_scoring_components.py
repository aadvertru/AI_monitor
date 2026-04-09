from __future__ import annotations

import unittest

from libs.analysis.scoring import (
    WEIGHT_SUM,
    compute_component_metrics,
    compute_final_score,
)


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

    def test_final_score_all_zero_components_returns_zero(self) -> None:
        components = {
            "visibility_score": 0.0,
            "prominence_score": 0.0,
            "sentiment_score": 0.0,
            "recommendation_score": 0.0,
            "source_quality_score": 0.0,
        }
        self.assertEqual(compute_final_score(components), 0.0)

    def test_final_score_all_one_components_returns_one(self) -> None:
        components = {
            "visibility_score": 1.0,
            "prominence_score": 1.0,
            "sentiment_score": 1.0,
            "recommendation_score": 1.0,
            "source_quality_score": 1.0,
        }
        self.assertEqual(compute_final_score(components), 1.0)

    def test_final_score_known_values_match_expected_formula(self) -> None:
        components = {
            "visibility_score": 1.0,
            "prominence_score": 0.6,
            "sentiment_score": 0.5,
            "recommendation_score": 0.8,
            "source_quality_score": 0.5,
        }
        self.assertEqual(compute_final_score(components), 0.72)

    def test_final_score_missing_fields_use_zero_substitution(self) -> None:
        components = {"visibility_score": 1.0}
        self.assertEqual(compute_final_score(components), 0.3)

    def test_final_score_rounding_is_stable_to_four_decimals(self) -> None:
        components = {
            "visibility_score": 0.33333,
            "prominence_score": 0.66667,
            "sentiment_score": 0.12345,
            "recommendation_score": 0.98765,
            "source_quality_score": 0.54321,
        }
        self.assertEqual(compute_final_score(components), 0.4938)

    def test_final_score_clamps_out_of_range_component_values(self) -> None:
        components = {
            "visibility_score": 5.0,
            "prominence_score": -1.0,
            "sentiment_score": 2.0,
            "recommendation_score": -3.0,
            "source_quality_score": 9.0,
        }
        self.assertEqual(compute_final_score(components), 0.6)

    def test_weight_constants_sum_to_one(self) -> None:
        self.assertEqual(WEIGHT_SUM, 1.0)


if __name__ == "__main__":
    unittest.main()
