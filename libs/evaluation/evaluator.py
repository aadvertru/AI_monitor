"""Answer evaluation service contracts and deterministic test evaluator."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Protocol

from libs.execution.safe_logging import log_event
from libs.storage.models import AnswerEvaluationVerdict, BrandFact

logger = logging.getLogger(__name__)

MOCK_EVALUATION_VERSION = "mock-evaluator-v1"


@dataclass(frozen=True)
class AnswerEvaluationInput:
    audit_id: int
    run_id: int
    query_text: str
    answer_text: str
    brand_facts: list[BrandFact]
    level: str
    model_id: str


@dataclass(frozen=True)
class AnswerEvaluationResult:
    verdict: AnswerEvaluationVerdict
    evaluation_version: str
    rationale: str | None = None
    confidence: float | None = None

    def to_json_safe(self) -> dict[str, str | float | None]:
        payload = asdict(self)
        payload["verdict"] = self.verdict.value
        return payload


class AnswerEvaluator(Protocol):
    async def evaluate(self, input_data: AnswerEvaluationInput) -> AnswerEvaluationResult:
        """Evaluate one normalized provider answer against audit-scoped brand facts."""


class MockAnswerEvaluator:
    """Deterministic evaluator for tests and local development."""

    async def evaluate(self, input_data: AnswerEvaluationInput) -> AnswerEvaluationResult:
        answer = input_data.answer_text.strip()
        lower_answer = answer.lower()

        if not answer:
            return AnswerEvaluationResult(
                verdict=AnswerEvaluationVerdict.UNKNOWN,
                rationale="No answer text was available for evaluation.",
                confidence=0.0,
                evaluation_version=MOCK_EVALUATION_VERSION,
            )
        if "[correct]" in lower_answer:
            return AnswerEvaluationResult(
                verdict=AnswerEvaluationVerdict.CORRECT,
                rationale="Mock marker indicated a correct answer.",
                confidence=1.0,
                evaluation_version=MOCK_EVALUATION_VERSION,
            )
        if "[partial]" in lower_answer:
            return AnswerEvaluationResult(
                verdict=AnswerEvaluationVerdict.PARTIAL,
                rationale="Mock marker indicated a partially correct answer.",
                confidence=0.65,
                evaluation_version=MOCK_EVALUATION_VERSION,
            )
        if "[incorrect]" in lower_answer:
            return AnswerEvaluationResult(
                verdict=AnswerEvaluationVerdict.INCORRECT,
                rationale="Mock marker indicated an incorrect answer.",
                confidence=1.0,
                evaluation_version=MOCK_EVALUATION_VERSION,
            )
        return AnswerEvaluationResult(
            verdict=AnswerEvaluationVerdict.UNKNOWN,
            rationale="No mock evaluation marker was found.",
            confidence=0.25,
            evaluation_version=MOCK_EVALUATION_VERSION,
        )


async def evaluate_answer_safely(
    evaluator: AnswerEvaluator,
    input_data: AnswerEvaluationInput,
) -> AnswerEvaluationResult:
    """Run evaluator without exposing answer text, prompts, or brand descriptions."""
    try:
        return await evaluator.evaluate(input_data)
    except Exception as exc:
        log_event(
            logger,
            "answer_evaluation_failed",
            log_level=logging.WARNING,
            audit_id=input_data.audit_id,
            run_id=input_data.run_id,
            level=input_data.level,
            model_id=input_data.model_id,
            exception_type=exc.__class__.__name__,
        )
        return AnswerEvaluationResult(
            verdict=AnswerEvaluationVerdict.UNKNOWN,
            rationale="Answer evaluation failed safely.",
            confidence=None,
            evaluation_version=MOCK_EVALUATION_VERSION,
        )
