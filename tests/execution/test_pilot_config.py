from __future__ import annotations

import unittest

from libs.execution.pilot_config import (
    OPENAI_PILOT_API_FAMILY,
    PilotConfigError,
    PilotPolicyError,
    RealProviderPilotConfig,
    load_real_provider_pilot_config,
    validate_audit_against_pilot_config,
)


class RealProviderPilotConfigTests(unittest.TestCase):
    def test_mock_provider_mode_is_default(self) -> None:
        config = load_real_provider_pilot_config(env={})

        self.assertFalse(config.real_provider_enabled)
        self.assertEqual(config.provider_mode, "mock")
        self.assertEqual(config.max_providers, 1)
        self.assertEqual(config.max_queries, 5)
        self.assertEqual(config.max_runs_per_query, 1)
        self.assertEqual(config.max_total_runs, 5)
        self.assertEqual(config.openai_api_family, OPENAI_PILOT_API_FAMILY)

    def test_real_provider_execution_is_blocked_when_disabled(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Real provider execution is disabled"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "false"}
                ),
            )

    def test_mock_only_audit_is_allowed_in_openai_provider_mode(self) -> None:
        validate_audit_against_pilot_config(
            providers=["mock"],
            query_count=10,
            runs_per_query=5,
            scdl_level="L2",
            config=load_real_provider_pilot_config(
                env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
            ),
        )

    def test_mixed_provider_lists_are_rejected_in_real_provider_mode(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "mixed provider lists"):
            validate_audit_against_pilot_config(
                providers=["mock", "openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_max_providers_per_real_audit_is_enforced(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "max providers"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openai",
                    max_providers=0,
                ),
            )

    def test_max_queries_per_real_audit_is_enforced(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "max queries"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=6,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_max_runs_per_query_is_enforced(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "max runs per query"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=2,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_max_total_real_runs_is_enforced(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "max total runs"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=2,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={
                        "PROVIDER_MODE": "openai",
                        "REAL_PROVIDER_ENABLED": "true",
                        "REAL_PROVIDER_MAX_TOTAL_RUNS": "1",
                    }
                ),
            )

    def test_unsupported_provider_mode_returns_controlled_error(self) -> None:
        with self.assertRaisesRegex(PilotConfigError, "PROVIDER_MODE"):
            load_real_provider_pilot_config(env={"PROVIDER_MODE": "gemini"})

    def test_unsupported_provider_execution_returns_controlled_error(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Unsupported real-provider"):
            validate_audit_against_pilot_config(
                providers=["gemini"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_anthropic_provider_mode_allows_anthropic_l1_execution(self) -> None:
        validate_audit_against_pilot_config(
            providers=["anthropic"],
            query_count=1,
            runs_per_query=1,
            scdl_level="L1",
            config=load_real_provider_pilot_config(
                env={"PROVIDER_MODE": "anthropic", "REAL_PROVIDER_ENABLED": "true"}
            ),
        )

    def test_anthropic_l2_is_allowed_to_reach_adapter_for_unsupported_l2_error(self) -> None:
        validate_audit_against_pilot_config(
            providers=["anthropic"],
            query_count=1,
            runs_per_query=1,
            scdl_level="L2",
            config=load_real_provider_pilot_config(
                env={"PROVIDER_MODE": "anthropic", "REAL_PROVIDER_ENABLED": "true"}
            ),
        )

    def test_openrouter_provider_mode_allows_openrouter_l1_and_l2_execution(self) -> None:
        for scdl_level in ("L1", "L2"):
            validate_audit_against_pilot_config(
                providers=["openrouter"],
                query_count=1,
                runs_per_query=1,
                scdl_level=scdl_level,
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openrouter", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_provider_mode_mismatch_rejects_anthropic_openai_and_openrouter(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "Provider mode 'openai'"):
            validate_audit_against_pilot_config(
                providers=["anthropic"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openai", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

        with self.assertRaisesRegex(PilotPolicyError, "Provider mode 'anthropic'"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "anthropic", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

        with self.assertRaisesRegex(PilotPolicyError, "Provider mode 'openrouter'"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(
                    env={"PROVIDER_MODE": "openrouter", "REAL_PROVIDER_ENABLED": "true"}
                ),
            )

    def test_mock_mode_rejects_openai_execution(self) -> None:
        with self.assertRaisesRegex(PilotPolicyError, "mock execution only"):
            validate_audit_against_pilot_config(
                providers=["openai"],
                query_count=1,
                runs_per_query=1,
                scdl_level="L1",
                config=load_real_provider_pilot_config(env={}),
            )

    def test_mock_provider_path_remains_allowed_by_default(self) -> None:
        validate_audit_against_pilot_config(
            providers=["mock"],
            query_count=5,
            runs_per_query=5,
            scdl_level="L2",
            config=load_real_provider_pilot_config(env={}),
        )

    def test_task_does_not_configure_real_openai_api_calls(self) -> None:
        self.assertEqual(OPENAI_PILOT_API_FAMILY, "responses_api")


if __name__ == "__main__":
    unittest.main()
