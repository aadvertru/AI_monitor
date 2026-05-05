from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libs.storage.models import Audit, AuditTarget, Base, Brand, SCDLLevel


class AuditTargetModelTests(unittest.TestCase):
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

    def _create_audit(self) -> Audit:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openrouter"], runs_per_query=1)
        self.session.add_all([brand, audit])
        self.session.commit()
        return audit

    def _target(self, audit: Audit, **overrides) -> AuditTarget:
        values = {
            "audit_id": audit.id,
            "ai_family": "chatgpt",
            "execution_provider": "openrouter",
            "model_provider": "openai",
            "model_id": "openai/gpt-4o-mini",
            "display_name": "GPT-4o mini",
            "level": SCDLLevel.L1,
            "gateway": True,
            "gateway_l2_experimental": False,
        }
        values.update(overrides)
        return AuditTarget(**values)

    def test_target_can_be_created_for_audit(self) -> None:
        audit = self._create_audit()
        target = self._target(audit)

        self.session.add(target)
        self.session.commit()

        self.assertIsNotNone(target.id)
        self.assertEqual(target.audit_id, audit.id)
        self.assertEqual(target.level, SCDLLevel.L1)
        self.assertEqual(audit.targets, [target])

    def test_required_fields_are_enforced_by_storage_layer(self) -> None:
        audit = self._create_audit()
        required_fields = [
            "audit_id",
            "ai_family",
            "execution_provider",
            "model_provider",
            "model_id",
            "display_name",
            "level",
        ]

        for field_name in required_fields:
            with self.subTest(field_name=field_name):
                target = self._target(audit, **{field_name: None})
                self.session.add(target)
                with self.assertRaises(IntegrityError):
                    self.session.commit()
                self.session.rollback()

    def test_invalid_level_is_rejected_by_constraint(self) -> None:
        audit = self._create_audit()
        target = self._target(audit, level="L3")

        self.session.add(target)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_gateway_l2_experimental_is_rejected_for_l1(self) -> None:
        audit = self._create_audit()
        target = self._target(
            audit,
            level=SCDLLevel.L1,
            gateway_l2_experimental=True,
        )

        self.session.add(target)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_gateway_l2_experimental_is_accepted_for_l2(self) -> None:
        audit = self._create_audit()
        target = self._target(
            audit,
            level=SCDLLevel.L2,
            gateway_l2_experimental=True,
        )

        self.session.add(target)
        self.session.commit()

        self.assertIsNotNone(target.id)
        self.assertEqual(target.level, SCDLLevel.L2)
        self.assertTrue(target.gateway_l2_experimental)

    def test_targets_are_deleted_with_audit(self) -> None:
        audit = self._create_audit()
        target = self._target(audit)
        self.session.add(target)
        self.session.commit()

        target_id = target.id
        self.session.delete(audit)
        self.session.commit()

        self.assertIsNone(self.session.get(AuditTarget, target_id))

    def test_legacy_audit_without_targets_still_loads(self) -> None:
        audit = self._create_audit()

        loaded = self.session.get(Audit, audit.id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.targets, [])


if __name__ == "__main__":
    unittest.main()
