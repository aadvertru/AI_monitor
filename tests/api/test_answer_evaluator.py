from __future__ import annotations

import unittest

from libs.evaluation.evaluator import (
    MOCK_EVALUATION_VERSION,
    AnswerEvaluationInput,
    AnswerEvaluationResult,
    MockAnswerEvaluator,
    evaluate_answer_safely,
)
from libs.storage.models import (
    AnswerEvaluationVerdict,
    BrandFact,
    BrandFactSource,
    BrandFactType,
)


def _input(answer_text: str) -> AnswerEvaluationInput:
    return AnswerEvaluationInput(
        audit_id=1,
        run_id=10,
        query_text="Who is Acme?",
        answer_text=answer_text,
        brand_facts=[
            BrandFact(
                audit_id=1,
                fact_text="Brand name: Acme",
                fact_type=BrandFactType.BRAND_NAME,
                source=BrandFactSource.BRAND_NAME,
                confidence=1.0,
            )
        ],
        level="L1",
        model_id="mock-model",
    )


class AnswerEvaluatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_evaluator_returns_correct_verdict(self) -> None:
        result = await MockAnswerEvaluator().evaluate(_input("Acme is visible. [CORRECT]"))

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.CORRECT)
        self.assertEqual(result.evaluation_version, MOCK_EVALUATION_VERSION)
        self.assertEqual(result.confidence, 1.0)

    async def test_mock_evaluator_returns_partial_verdict(self) -> None:
        result = await MockAnswerEvaluator().evaluate(_input("Some facts match. [PARTIAL]"))

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.PARTIAL)
        self.assertIsNotNone(result.rationale)

    async def test_mock_evaluator_returns_incorrect_verdict(self) -> None:
        result = await MockAnswerEvaluator().evaluate(_input("Wrong facts. [INCORRECT]"))

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.INCORRECT)

    async def test_mock_evaluator_handles_empty_answer(self) -> None:
        result = await MockAnswerEvaluator().evaluate(_input("  "))

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.UNKNOWN)
        self.assertEqual(result.confidence, 0.0)

    async def test_evaluation_output_is_json_safe(self) -> None:
        result = AnswerEvaluationResult(
            verdict=AnswerEvaluationVerdict.CORRECT,
            rationale="Safe rationale.",
            confidence=0.8,
            evaluation_version="eval-v1",
        )

        payload = result.to_json_safe()

        self.assertEqual(payload["verdict"], "correct")
        self.assertEqual(payload["evaluation_version"], "eval-v1")
        self.assertNotIn("answer_text", payload)
        self.assertNotIn("brand_facts", payload)

    async def test_no_raw_provider_response_is_required(self) -> None:
        input_data = _input("[CORRECT]")

        result = await MockAnswerEvaluator().evaluate(input_data)

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.CORRECT)
        self.assertFalse(hasattr(input_data, "raw_response"))

    async def test_safe_wrapper_does_not_log_answer_text_or_brand_description(self) -> None:
        class RaisingEvaluator:
            async def evaluate(
                self, input_data: AnswerEvaluationInput
            ) -> AnswerEvaluationResult:
                raise RuntimeError("boom")

        input_data = _input("secret answer text [CORRECT]")
        with self.assertLogs("libs.evaluation.evaluator", level="WARNING") as logs:
            result = await evaluate_answer_safely(RaisingEvaluator(), input_data)

        self.assertEqual(result.verdict, AnswerEvaluationVerdict.UNKNOWN)
        log_output = "\n".join(logs.output)
        self.assertIn("answer_evaluation_failed", log_output)
        self.assertNotIn("secret answer text", log_output)
        self.assertNotIn("Brand name: Acme", log_output)


if __name__ == "__main__":
    unittest.main()
