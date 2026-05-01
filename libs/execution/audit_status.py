"""Audit status transition rules for execution pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass

from libs.storage.models import AuditStatus


@dataclass(frozen=True)
class AuditFinalStatusInputs:
    expected_runs: int
    terminal_runs: int
    usable_score_count: int
    terminal_failure_count: int = 0
    execution_error_count: int = 0
    processing_error_count: int = 0
    missing_raw_count: int = 0
    fatal_error: bool = False


def derive_final_audit_status(inputs: AuditFinalStatusInputs) -> AuditStatus:
    """Derive final audit status after execution and post-processing.

    Status meanings:
    - completed: all expected runs are terminal and accounted for; brand may be absent.
    - partial: at least one usable result exists, but some run/process failed or skipped.
    - failed: fatal error or terminal completion with no usable scored data.
    - running: expected work is still not terminal/accounted for.
    """
    if inputs.fatal_error:
        return AuditStatus.FAILED

    has_recoverable_errors = (
        inputs.terminal_failure_count > 0
        or inputs.execution_error_count > 0
        or inputs.processing_error_count > 0
        or inputs.missing_raw_count > 0
    )
    has_usable_data = inputs.usable_score_count > 0
    all_expected_terminal = (
        inputs.expected_runs > 0 and inputs.terminal_runs >= inputs.expected_runs
    )

    if not has_usable_data and (
        inputs.terminal_failure_count > 0
        or inputs.execution_error_count > 0
        or all_expected_terminal
    ):
        return AuditStatus.FAILED

    if has_recoverable_errors:
        return AuditStatus.PARTIAL

    if all_expected_terminal:
        return AuditStatus.COMPLETED

    return AuditStatus.RUNNING
