from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    AuditCreateRequest,
    archive_audit,
    create_audit,
    delete_audit,
    list_audits,
    restore_audit,
)
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import Audit, Base, Brand, Query, User, UserRole

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class AuditArchiveAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(self, email: str) -> User:
        async with self.session_factory() as session:
            user = User(
                email=email,
                hashed_password="hashed-password",
                role=UserRole.USER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    def _authenticated_request(self, user: User) -> Request:
        config = load_auth_config(env=AUTH_ENV)
        token = create_access_token(user_id=user.id, role=user.role.value, config=config)
        return Request(
            {
                "type": "http",
                "headers": [(b"cookie", f"{config.cookie.name}={token}".encode("ascii"))],
            }
        )

    async def _create_audit(self, user: User, brand_name: str = "Acme AI") -> int:
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": brand_name,
                "brand_domain": "acme.example",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["best ai visibility tools"],
            }
        )
        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )
        return result.audit_id

    async def test_archive_owner_audit_hides_it_from_active_list(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await archive_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(result.audit_id, audit_id)
        self.assertIsNotNone(result.archived_at)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                active = await list_audits(
                    request=self._authenticated_request(owner),
                    archived=False,
                    session=session,
                )
                archived = await list_audits(
                    request=self._authenticated_request(owner),
                    archived=True,
                    session=session,
                )

        self.assertEqual(active, [])
        self.assertEqual([audit.audit_id for audit in archived], [audit_id])

    async def test_restore_owner_audit_returns_it_to_active_list(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                await archive_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await restore_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertIsNone(result.archived_at)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                active = await list_audits(
                    request=self._authenticated_request(owner),
                    archived=False,
                    session=session,
                )

        self.assertEqual([audit.audit_id for audit in active], [audit_id])

    async def test_delete_archived_audit_removes_audit_owned_data_but_keeps_brand(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit(owner)

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                await archive_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )
                response = await delete_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(response.status_code, 204)
        async with self.session_factory() as session:
            self.assertIsNone(await session.get(Audit, audit_id))
            query_rows = (
                await session.execute(select(Query).where(Query.audit_id == audit_id))
            ).scalars().all()
            self.assertEqual(query_rows, [])
            brands = (await session.execute(select(Brand))).scalars().all()
            self.assertEqual(len(brands), 1)
            self.assertEqual(brands[0].name, "Acme AI")

    async def test_delete_active_audit_is_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        audit_id = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await delete_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)

    async def test_cross_user_archive_restore_and_delete_are_rejected(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit_id = await self._create_audit(owner)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as archive_context,
            ):
                await archive_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                await archive_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as restore_context,
            ):
                await restore_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as delete_context,
            ):
                await delete_audit(
                    audit_id=audit_id,
                    request=self._authenticated_request(other),
                    session=session,
                )

        self.assertEqual(archive_context.exception.status_code, 404)
        self.assertEqual(restore_context.exception.status_code, 404)
        self.assertEqual(delete_context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
