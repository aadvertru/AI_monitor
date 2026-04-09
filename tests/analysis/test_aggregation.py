from __future__ import annotations

import unittest

from libs.analysis.aggregation import compute_query_score


class AggregationTests(unittest.TestCase):
    def test_three_successful_runs_average_correctly(self) -> None:
        run_results = [
            {"status": "success", "final_score": 0.6},
            {"status": "success", "final_score": 0.8},
            {"status": "success", "final_score": 1.0},
        ]

        self.assertEqual(compute_query_score(run_results), 0.8)

    def test_mixed_statuses_average_only_successful_runs(self) -> None:
        run_results = [
            {"status": "success", "final_score": 0.5},
            {"status": "error", "final_score": 0.9},
            {"status": "timeout", "final_score": 0.7},
            {"status": "success", "final_score": 0.3},
        ]

        self.assertEqual(compute_query_score(run_results), 0.4)

    def test_no_successful_runs_returns_none(self) -> None:
        run_results = [
            {"status": "error", "final_score": 0.5},
            {"status": "timeout", "final_score": 0.8},
            {"status": "rate_limited", "final_score": 0.3},
        ]

        self.assertIsNone(compute_query_score(run_results))

    def test_empty_list_returns_none(self) -> None:
        self.assertIsNone(compute_query_score([]))

    def test_single_successful_run_returns_its_score(self) -> None:
        run_results = [{"status": "success", "final_score": 0.7345}]
        self.assertEqual(compute_query_score(run_results), 0.7345)

    def test_known_inputs_return_exact_rounded_average(self) -> None:
        run_results = [
            {"status": "success", "final_score": 0.3333},
            {"status": "success", "final_score": 0.6666},
        ]

        self.assertEqual(compute_query_score(run_results), 0.5)

    def test_malformed_input_returns_none(self) -> None:
        run_results = [
            {"status": "success", "final_score": "bad"},
            {"status": "success", "final_score": 0.7},
        ]

        self.assertIsNone(compute_query_score(run_results))


if __name__ == "__main__":
    unittest.main()
