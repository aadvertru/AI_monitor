from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from libs.execution.provider_adapter import ProviderResponse
from libs.storage.models import Audit, Base, Brand, Query, Run, RunStatus
from libs.storage.raw_response_storage import (
    RawResponseAlreadyExistsError,
    store_raw_response_for_run,
)


class RawResponseStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session = Session(bind=self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _create_run(self) -> Run:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openai"], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring tools")
        run = Run(
            audit=audit,
            query=query,
            provider="openai",
            run_number=1,
            status=RunStatus.PENDING,
        )
        self.session.add_all([brand, audit, query, run])
        self.session.commit()
        return run

    def test_raw_response_is_stored_correctly_happy_path(self) -> None:
        run = self._create_run()
        response = ProviderResponse(
            status="success",
            raw_answer="Acme AI appears in results.",
            citations=[{"url": "https://example.com", "title": "Example"}],
            response_time=0.42,
            error=None,
            provider_metadata={"provider": "openai", "model": "gpt-4.1-mini"},
        )

        raw = store_raw_response_for_run(
            self.session,
            run_id=run.id,
            provider_response=response,
            request_snapshot={"query": "best ai monitoring tools", "provider": "openai"},
        )
        self.session.commit()

        self.assertIsNotNone(raw.id)
        self.assertEqual(raw.run_id, run.id)
        self.assertEqual(raw.provider_status, "success")
        self.assertEqual(raw.raw_answer, "Acme AI appears in results.")
        self.assertEqual(raw.response_time, 0.42)
        self.assertEqual(raw.citations, [{"url": "https://example.com", "title": "Example"}])
        self.assertEqual(raw.error_object, None)
        self.assertEqual(raw.request_snapshot["provider"], "openai")

    def test_error_raw_response_is_stored_correctly(self) -> None:
        run = self._create_run()
        response = ProviderResponse(
            status="error",
            raw_answer=None,
            citations=None,
            response_time=0.11,
            error={"code": "provider_error", "message": "Request failed."},
            provider_metadata={"provider": "openai"},
        )

        raw = store_raw_response_for_run(
            self.session,
            run_id=run.id,
            provider_response=response,
            request_snapshot={"query": "best ai monitoring tools", "provider": "openai"},
        )
        self.session.commit()

        self.assertEqual(raw.provider_status, "error")
        self.assertIsNone(raw.raw_answer)
        self.assertEqual(raw.error_object, {"code": "provider_error", "message": "Request failed."})
        self.assertEqual(raw.provider_metadata, {"provider": "openai"})

    def test_no_overwrite_behavior_is_enforced(self) -> None:
        run = self._create_run()
        first = ProviderResponse(
            status="success",
            raw_answer="first",
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={"provider": "openai"},
        )
        second = ProviderResponse(
            status="success",
            raw_answer="second",
            citations=[],
            response_time=0.2,
            error=None,
            provider_metadata={"provider": "openai"},
        )

        store_raw_response_for_run(
            self.session,
            run_id=run.id,
            provider_response=first,
            request_snapshot={"query": "q"},
        )
        self.session.commit()

        with self.assertRaises(RawResponseAlreadyExistsError):
            store_raw_response_for_run(
                self.session,
                run_id=run.id,
                provider_response=second,
                request_snapshot={"query": "q"},
            )
        self.session.rollback()

        persisted = self.session.get(Run, run.id)
        assert persisted is not None
        assert persisted.raw_response is not None
        self.assertEqual(persisted.raw_response.raw_answer, "first")
        self.assertEqual(persisted.raw_response.response_time, 0.1)

    def test_empty_raw_answer_still_creates_valid_record(self) -> None:
        run = self._create_run()
        response = ProviderResponse(
            status="success",
            raw_answer="",
            citations=[],
            response_time=0.2,
            error=None,
            provider_metadata={"provider": "openai"},
        )

        raw = store_raw_response_for_run(
            self.session,
            run_id=run.id,
            provider_response=response,
            request_snapshot={"query": "q", "provider": "openai"},
        )
        self.session.commit()

        self.assertEqual(raw.raw_answer, "")
        self.assertEqual(raw.citations, [])
        self.assertEqual(raw.provider_status, "success")
        self.assertEqual(raw.error_object, None)


if __name__ == "__main__":
    unittest.main()

