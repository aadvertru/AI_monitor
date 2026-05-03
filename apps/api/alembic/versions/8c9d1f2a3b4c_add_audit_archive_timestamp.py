"""add audit archive timestamp

Revision ID: 8c9d1f2a3b4c
Revises: 0bd42c15e942
Create Date: 2026-05-02 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c9d1f2a3b4c"
down_revision: str | None = "0bd42c15e942"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("audits") as batch_op:
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("audits") as batch_op:
        batch_op.drop_column("archived_at")
