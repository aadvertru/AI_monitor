from __future__ import annotations

import logging
import unittest

from libs.execution.safe_logging import log_event, provider_log_fields


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class SafeLoggingTests(unittest.TestCase):
    def test_log_event_keeps_only_allowlisted_safe_fields(self) -> None:
        logger = logging.getLogger("tests.safe_logging")
        handler = _ListHandler()
        previous_level = logger.level
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        try:
            log_event(
                logger,
                "provider_call_started",
                audit_id=1,
                execution_provider="openrouter",
                prompt="do not log me",
                headers={"authorization": "Bearer sk-or-secret"},
                raw_response="secret",
                error_code="NO_API_KEY",
            )
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

        self.assertEqual(len(handler.records), 1)
        record = handler.records[0]
        self.assertEqual(record.event, "provider_call_started")
        self.assertEqual(record.audit_id, 1)
        self.assertEqual(record.execution_provider, "openrouter")
        self.assertEqual(record.error_code, "NO_API_KEY")
        self.assertNotIn("prompt", record.__dict__)
        self.assertNotIn("headers", record.__dict__)
        self.assertNotIn("raw_response", record.__dict__)

    def test_provider_log_fields_extracts_openrouter_gateway_metadata(self) -> None:
        fields = provider_log_fields(
            "gemini",
            metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "google/gemini-2.0-flash-001",
                "model_provider": "google",
                "gateway": True,
                "gateway_l2_experimental": True,
                "level": "L2",
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            },
            citations=[{"url": "https://example.com"}],
        )

        self.assertEqual(fields["execution_provider"], "openrouter")
        self.assertEqual(fields["model_id"], "google/gemini-2.0-flash-001")
        self.assertEqual(fields["model_provider"], "google")
        self.assertTrue(fields["gateway"])
        self.assertTrue(fields["gateway_l2_experimental"])
        self.assertEqual(fields["level"], "L2")
        self.assertEqual(fields["source_count"], 1)
        self.assertEqual(fields["total_tokens"], 30)


if __name__ == "__main__":
    unittest.main()
