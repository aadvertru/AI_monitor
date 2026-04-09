from __future__ import annotations

import unittest

from libs.control.query_capping import DEFAULT_MAX_QUERIES, cap_queries


class QueryCappingTests(unittest.TestCase):
    def test_longer_list_is_capped_to_first_n(self) -> None:
        queries = ["q1", "q2", "q3", "q4", "q5"]
        self.assertEqual(cap_queries(queries, max_queries=3), ["q1", "q2", "q3"])

    def test_equal_length_to_cap_is_unchanged(self) -> None:
        queries = ["q1", "q2", "q3"]
        self.assertEqual(cap_queries(queries, max_queries=3), ["q1", "q2", "q3"])

    def test_shorter_list_than_cap_is_unchanged(self) -> None:
        queries = ["q1", "q2"]
        self.assertEqual(cap_queries(queries, max_queries=5), ["q1", "q2"])

    def test_none_max_queries_uses_default_cap(self) -> None:
        queries = [f"q{i}" for i in range(60)]
        capped = cap_queries(queries, max_queries=None)
        self.assertEqual(len(capped), DEFAULT_MAX_QUERIES)
        self.assertEqual(capped, queries[:DEFAULT_MAX_QUERIES])


if __name__ == "__main__":
    unittest.main()

