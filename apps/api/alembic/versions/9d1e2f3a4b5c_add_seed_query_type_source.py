"""add seed query type and source

Revision ID: 9d1e2f3a4b5c
Revises: 8c9d1f2a3b4c
Create Date: 2026-05-02 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9d1e2f3a4b5c"
down_revision: str | None = "8c9d1f2a3b4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("queries") as batch_op:
        batch_op.add_column(sa.Column("query_type", sa.String(length=64), nullable=True))
        batch_op.add_column(
            sa.Column(
                "source",
                sa.String(length=16),
                server_default="user",
                nullable=False,
            )
        )

    with op.batch_alter_table("queries") as batch_op:
        batch_op.alter_column("source", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("queries") as batch_op:
        batch_op.drop_column("source")
        batch_op.drop_column("query_type")
