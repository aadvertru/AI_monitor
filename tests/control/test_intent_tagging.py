from __future__ import annotations

import unittest

from libs.control.intent_tagging import (
    INTENT_COMPARISON,
    INTENT_GENERAL,
    INTENT_USE_CASE,
    tag_query_intent,
)


class IntentTaggingTests(unittest.TestCase):
    def test_best_query_maps_to_comparison(self) -> None:
        self.assertEqual(tag_query_intent("best ai visibility tools"), INTENT_COMPARISON)

    def test_how_query_maps_to_use_case(self) -> None:
        self.assertEqual(tag_query_intent("how to improve brand visibility"), INTENT_USE_CASE)

    def test_unmatched_query_maps_to_general(self) -> None:
        self.assertEqual(tag_query_intent("ai brand visibility metrics"), INTENT_GENERAL)

    def test_casing_differences_match_rules(self) -> None:
        self.assertEqual(tag_query_intent("BEST options"), INTENT_COMPARISON)
        self.assertEqual(tag_query_intent("How to benchmark"), INTENT_USE_CASE)
        self.assertEqual(tag_query_intent("HOW TO benchmark"), INTENT_USE_CASE)

    def test_best_inside_long_phrase_still_matches(self) -> None:
        query = "the best monitoring tools for brand visibility"
        self.assertEqual(tag_query_intent(query), INTENT_COMPARISON)


if __name__ == "__main__":
    unittest.main()

