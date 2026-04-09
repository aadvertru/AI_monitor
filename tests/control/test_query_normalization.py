from __future__ import annotations

import unittest

from libs.control.query_normalization import normalize_seed_queries


class QueryNormalizationTests(unittest.TestCase):
    def test_mixed_input_normalizes_deterministically(self) -> None:
        source = ["  First Query  ", "SeCoNd", "  Third   Query "]

        normalized = normalize_seed_queries(source)

        self.assertEqual(normalized, ["first query", "second", "third   query"])
        self.assertEqual(source, ["  First Query  ", "SeCoNd", "  Third   Query "])

    def test_empty_strings_are_removed(self) -> None:
        normalized = normalize_seed_queries(["", "valid", "", "  OK  "])
        self.assertEqual(normalized, ["valid", "ok"])

    def test_whitespace_only_entries_are_removed(self) -> None:
        normalized = normalize_seed_queries(["   ", "\t", "\n", "  Query  "])
        self.assertEqual(normalized, ["query"])


if __name__ == "__main__":
    unittest.main()

