from __future__ import annotations

import unittest

from libs.analysis.aggregation import (
    CRITICAL_SCORE_THRESHOLD,
    build_audit_summary,
    compute_provider_scores,
    compute_query_score,
    find_critical_queries,
)


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

    def test_provider_scores_malformed_rows_are_skipped(self) -> None:
        run_results = [
            {"provider": "openai", "status": "success", "final_score": 0.8},
            {"provider": None, "status": "success", "final_score": 0.7},
        ]

        self.assertEqual(compute_provider_scores(run_results), {"openai": 0.8})

    def test_provider_scores_all_malformed_rows_return_empty_dict(self) -> None:
        run_results = [
            {"provider": None, "status": "success", "final_score": 0.7},
            {"provider": 123, "status": "error", "final_score": 0.2},
            "bad-row",
        ]

        self.assertEqual(compute_provider_scores(run_results), {})

    def test_build_audit_summary_happy_path_multiple_queries_providers(self) -> None:
        run_results = [
            {
                "query": "q1",
                "provider": "openai",
                "status": "success",
                "final_score": 0.9,
                "visible_brand": True,
            },
            {
                "query": "q1",
                "provider": "mock",
                "status": "success",
                "final_score": 0.3,
                "visible_brand": False,
            },
            {
                "query": "q1",
                "provider": "openai",
                "status": "error",
                "final_score": 0.7,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "openai",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "mock",
                "status": "success",
                "final_score": 0.4,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "mock",
                "status": "timeout",
                "final_score": 0.5,
                "visible_brand": False,
            },
            {
                "query": "q3",
                "provider": "openai",
                "status": "error",
                "final_score": 0.1,
                "visible_brand": False,
            },
            {
                "query": "q3",
                "provider": "mock",
                "status": "rate_limited",
                "final_score": 0.1,
                "visible_brand": False,
            },
        ]

        summary = build_audit_summary(run_results)

        self.assertEqual(summary["total_queries"], 3)
        self.assertEqual(summary["total_runs"], 8)
        self.assertEqual(summary["successful_runs"], 4)
        self.assertEqual(summary["failed_runs"], 4)
        self.assertEqual(summary["completion_ratio"], 0.5)
        self.assertEqual(summary["visibility_ratio"], 0.25)
        self.assertEqual(summary["average_score"], 0.45)
        self.assertEqual(summary["critical_query_count"], 2)
        self.assertEqual(
            summary["provider_scores"],
            {
                "mock": 0.35,
                "openai": 0.55,
            },
        )

    def test_build_audit_summary_partial_audit_ratios(self) -> None:
        run_results = [
            {
                "query": "q1",
                "provider": "openai",
                "status": "success",
                "final_score": 0.6,
                "visible_brand": True,
            },
            {
                "query": "q1",
                "provider": "mock",
                "status": "error",
                "final_score": 0.0,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "openai",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": False,
            },
        ]

        summary = build_audit_summary(run_results)

        self.assertEqual(summary["completion_ratio"], 0.6667)
        self.assertEqual(summary["visibility_ratio"], 0.5)
        self.assertEqual(summary["average_score"], 0.4)
        self.assertEqual(summary["critical_query_count"], 1)
        self.assertEqual(summary["provider_scores"], {"mock": None, "openai": 0.4})

    def test_build_audit_summary_all_failed_runs(self) -> None:
        run_results = [
            {
                "query": "q1",
                "provider": "openai",
                "status": "error",
                "final_score": 0.2,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "mock",
                "status": "timeout",
                "final_score": 0.4,
                "visible_brand": False,
            },
        ]

        summary = build_audit_summary(run_results)

        self.assertEqual(summary["total_runs"], 2)
        self.assertEqual(summary["successful_runs"], 0)
        self.assertEqual(summary["failed_runs"], 2)
        self.assertEqual(summary["completion_ratio"], 0.0)
        self.assertEqual(summary["visibility_ratio"], 0.0)
        self.assertIsNone(summary["average_score"])
        self.assertEqual(summary["critical_query_count"], 2)
        self.assertEqual(summary["provider_scores"], {"mock": None, "openai": None})

    def test_build_audit_summary_empty_runs_returns_safe_defaults(self) -> None:
        self.assertEqual(
            build_audit_summary([]),
            {
                "total_queries": 0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "completion_ratio": 0.0,
                "visibility_ratio": 0.0,
                "average_score": None,
                "critical_query_count": 0,
                "provider_scores": {},
            },
        )

    def test_build_audit_summary_known_input_exact_output(self) -> None:
        run_results = [
            {
                "query": "q1",
                "provider": "a",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": False,
            },
            {
                "query": "q1",
                "provider": "a",
                "status": "success",
                "final_score": 0.4,
                "visible_brand": False,
            },
            {
                "query": "q2",
                "provider": "b",
                "status": "error",
                "final_score": 0.9,
                "visible_brand": False,
            },
        ]

        self.assertEqual(
            build_audit_summary(run_results),
            {
                "total_queries": 2,
                "total_runs": 3,
                "successful_runs": 2,
                "failed_runs": 1,
                "completion_ratio": 0.6667,
                "visibility_ratio": 0.0,
                "average_score": 0.3,
                "critical_query_count": 2,
                "provider_scores": {"a": 0.3, "b": None},
            },
        )

    def test_build_audit_summary_malformed_input_returns_safe_defaults(self) -> None:
        malformed_run_results = [
            {
                "query": "q1",
                "provider": "openai",
                "status": "success",
                "final_score": 0.8,
                "visible_brand": "yes",
            }
        ]

        self.assertEqual(
            build_audit_summary(malformed_run_results),
            {
                "total_queries": 0,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "completion_ratio": 0.0,
                "visibility_ratio": 0.0,
                "average_score": None,
                "critical_query_count": 0,
                "provider_scores": {},
            },
        )

    def test_find_critical_queries_not_visible_reason(self) -> None:
        run_results = [
            {
                "query": "q_not_visible",
                "provider": "openai",
                "status": "success",
                "final_score": 0.9,
                "visible_brand": False,
            },
            {
                "query": "q_not_visible",
                "provider": "mock",
                "status": "error",
                "final_score": 0.1,
                "visible_brand": False,
            },
        ]

        self.assertEqual(
            find_critical_queries(run_results),
            [
                {
                    "query": "q_not_visible",
                    "reason": "not_visible",
                    "query_score": 0.9,
                }
            ],
        )

    def test_find_critical_queries_low_score_reason(self) -> None:
        run_results = [
            {
                "query": "q_low",
                "provider": "openai",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": True,
            },
            {
                "query": "q_low",
                "provider": "mock",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": True,
            },
        ]

        self.assertEqual(
            find_critical_queries(run_results),
            [
                {
                    "query": "q_low",
                    "reason": "low_score",
                    "query_score": 0.2,
                }
            ],
        )

    def test_find_critical_queries_no_successful_runs_reason(self) -> None:
        run_results = [
            {
                "query": "q_no_success",
                "provider": "openai",
                "status": "error",
                "final_score": 0.7,
                "visible_brand": True,
            },
            {
                "query": "q_no_success",
                "provider": "mock",
                "status": "timeout",
                "final_score": 0.4,
                "visible_brand": True,
            },
        ]

        self.assertEqual(
            find_critical_queries(run_results),
            [
                {
                    "query": "q_no_success",
                    "reason": "no_successful_runs",
                    "query_score": None,
                }
            ],
        )

    def test_find_critical_queries_score_exactly_threshold_is_not_critical(self) -> None:
        run_results = [
            {
                "query": "q_exact_threshold",
                "provider": "openai",
                "status": "success",
                "final_score": CRITICAL_SCORE_THRESHOLD,
                "visible_brand": True,
            }
        ]

        self.assertEqual(find_critical_queries(run_results), [])

    def test_find_critical_queries_score_just_below_threshold_is_critical(self) -> None:
        run_results = [
            {
                "query": "q_below_threshold",
                "provider": "openai",
                "status": "success",
                "final_score": 0.2999,
                "visible_brand": True,
            }
        ]

        self.assertEqual(
            find_critical_queries(run_results),
            [
                {
                    "query": "q_below_threshold",
                    "reason": "low_score",
                    "query_score": 0.2999,
                }
            ],
        )

    def test_find_critical_queries_visible_high_score_not_critical(self) -> None:
        run_results = [
            {
                "query": "q_good",
                "provider": "openai",
                "status": "success",
                "final_score": 0.8,
                "visible_brand": True,
            },
            {
                "query": "q_good",
                "provider": "mock",
                "status": "success",
                "final_score": 0.9,
                "visible_brand": True,
            },
        ]

        self.assertEqual(find_critical_queries(run_results), [])

    def test_find_critical_queries_empty_input_returns_empty_list(self) -> None:
        self.assertEqual(find_critical_queries([]), [])

    def test_find_critical_queries_skips_malformed_rows(self) -> None:
        run_results = [
            {
                "query": "q_low",
                "provider": "openai",
                "status": "success",
                "final_score": 0.2,
                "visible_brand": True,
            },
            {
                "query": "q_bad",
                "provider": "mock",
                "status": "success",
                "final_score": "bad",
                "visible_brand": True,
            },
            "not-a-dict",
        ]

        self.assertEqual(
            find_critical_queries(run_results),
            [
                {
                    "query": "q_low",
                    "reason": "low_score",
                    "query_score": 0.2,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
