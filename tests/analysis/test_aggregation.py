from __future__ import annotations

import unittest

from libs.analysis.aggregation import compute_provider_scores, compute_query_score


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

    def test_provider_scores_happy_path_two_providers(self) -> None:
        run_results = [
            {"provider": "openai", "status": "success", "final_score": 0.8},
            {"provider": "openai", "status": "success", "final_score": 0.6},
            {"provider": "mock", "status": "success", "final_score": 0.5},
            {"provider": "mock", "status": "success", "final_score": 0.7},
        ]

        self.assertEqual(
            compute_provider_scores(run_results),
            {
                "mock": 0.6,
                "openai": 0.7,
            },
        )

    def test_provider_with_only_failed_runs_returns_none(self) -> None:
        run_results = [
            {"provider": "openai", "status": "success", "final_score": 0.8},
            {"provider": "mock", "status": "error", "final_score": 0.4},
            {"provider": "mock", "status": "timeout", "final_score": 0.2},
        ]

        self.assertEqual(
            compute_provider_scores(run_results),
            {
                "mock": None,
                "openai": 0.8,
            },
        )

    def test_provider_scores_mixed_statuses_average_success_only(self) -> None:
        run_results = [
            {"provider": "openai", "status": "success", "final_score": 0.9},
            {"provider": "openai", "status": "error", "final_score": 0.2},
            {"provider": "openai", "status": "success", "final_score": 0.3},
            {"provider": "mock", "status": "rate_limited", "final_score": 0.9},
            {"provider": "mock", "status": "success", "final_score": 0.4},
        ]

        self.assertEqual(
            compute_provider_scores(run_results),
            {
                "mock": 0.4,
                "openai": 0.6,
            },
        )

    def test_provider_scores_empty_input_returns_empty_dict(self) -> None:
        self.assertEqual(compute_provider_scores([]), {})

    def test_provider_scores_known_values_exact(self) -> None:
        run_results = [
            {"provider": "a", "status": "success", "final_score": 0.1112},
            {"provider": "a", "status": "success", "final_score": 0.2222},
            {"provider": "b", "status": "success", "final_score": 0.3333},
            {"provider": "b", "status": "success", "final_score": 0.6667},
        ]

        self.assertEqual(
            compute_provider_scores(run_results),
            {
                "a": 0.1667,
                "b": 0.5,
            },
        )

    def test_provider_scores_keys_are_sorted_alphabetically(self) -> None:
        run_results = [
            {"provider": "zeta", "status": "success", "final_score": 0.7},
            {"provider": "alpha", "status": "success", "final_score": 0.3},
        ]

        result = compute_provider_scores(run_results)
        self.assertEqual(list(result.keys()), ["alpha", "zeta"])

    def test_provider_scores_malformed_input_returns_empty_dict(self) -> None:
        run_results = [
            {"provider": "openai", "status": "success", "final_score": 0.8},
            {"provider": None, "status": "success", "final_score": 0.7},
        ]

        self.assertEqual(compute_provider_scores(run_results), {})


if __name__ == "__main__":
    unittest.main()
