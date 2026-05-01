from __future__ import annotations

import unittest

from libs.execution.audit_status import AuditFinalStatusInputs, derive_final_audit_status
from libs.storage.models import AuditStatus


class AuditStatusDecisionTests(unittest.TestCase):
    def test_completed_when_all_expected_runs_terminal_and_usable(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=1,
                terminal_runs=1,
                usable_score_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.COMPLETED)

    def test_brand_not_found_zero_score_still_counts_as_usable_scored_data(self) -> None:
        # Brand-not-found is represented by an existing Score row with final_score=0.0;
        # the status helper only needs the usable scored-row count.
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=1,
                terminal_runs=1,
                usable_score_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.COMPLETED)

    def test_processing_exception_without_any_scored_data_fails_closed(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=1,
                terminal_runs=1,
                usable_score_count=0,
                processing_error_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.FAILED)

    def test_partial_when_usable_data_exists_with_terminal_failure(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=2,
                terminal_runs=2,
                usable_score_count=1,
                terminal_failure_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.PARTIAL)

    def test_failed_when_no_usable_data_can_be_produced(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=1,
                terminal_runs=1,
                usable_score_count=0,
                terminal_failure_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.FAILED)

    def test_failed_when_fatal_error_occurs(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=1,
                terminal_runs=0,
                usable_score_count=0,
                fatal_error=True,
            )
        )

        self.assertEqual(status, AuditStatus.FAILED)

    def test_running_when_expected_work_is_not_terminal(self) -> None:
        status = derive_final_audit_status(
            AuditFinalStatusInputs(
                expected_runs=2,
                terminal_runs=1,
                usable_score_count=1,
            )
        )

        self.assertEqual(status, AuditStatus.RUNNING)


if __name__ == "__main__":
    unittest.main()
