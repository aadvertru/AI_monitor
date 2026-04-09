from __future__ import annotations

import unittest

from libs.analysis.mention_extraction import BrandMention
from libs.analysis.ranking import compute_brand_rank


class RankingTests(unittest.TestCase):
    def test_single_mention_returns_rank_one(self) -> None:
        mentions = [BrandMention(text="acme ai", sentence_index=0, char_offset=5)]
        self.assertEqual(compute_brand_rank(mentions), 1)

    def test_multiple_mentions_still_returns_rank_one(self) -> None:
        mentions = [
            BrandMention(text="acme ai", sentence_index=0, char_offset=1),
            BrandMention(text="acme ai", sentence_index=2, char_offset=8),
            BrandMention(text="acme ai", sentence_index=4, char_offset=3),
        ]
        self.assertEqual(compute_brand_rank(mentions), 1)

    def test_empty_mentions_returns_none(self) -> None:
        self.assertIsNone(compute_brand_rank([]))

    def test_repeated_calls_with_same_input_are_deterministic(self) -> None:
        mentions = [
            BrandMention(text="acme ai", sentence_index=1, char_offset=4),
            BrandMention(text="acme ai", sentence_index=2, char_offset=10),
        ]
        first = compute_brand_rank(mentions)
        second = compute_brand_rank(mentions)
        self.assertEqual(first, second)
        self.assertEqual(first, 1)


if __name__ == "__main__":
    unittest.main()

