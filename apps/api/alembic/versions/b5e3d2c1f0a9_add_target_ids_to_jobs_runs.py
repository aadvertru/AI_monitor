"""add target ids to jobs and runs

Revision ID: b5e3d2c1f0a9
Revises: a4f2c1d8e9b0
Create Date: 2026-05-05 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5e3d2c1f0a9"
down_revision: str | None = "a4f2c1d8e9b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("audit_target_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_jobs_audit_target_id_audit_targets",
            "audit_targets",
            ["audit_target_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint("uq_runs_execution_identity", type_="unique")
        batch_op.add_column(sa.Column("audit_target_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_runs_audit_target_id_audit_targets",
            "audit_targets",
            ["audit_target_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "uq_runs_execution_identity",
            ["audit_id", "query_id", "audit_target_id", "provider", "run_number"],
        )


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint("uq_runs_execution_identity", type_="unique")
        batch_op.drop_constraint("fk_runs_audit_target_id_audit_targets", type_="foreignkey")
        batch_op.drop_column("audit_target_id")
        batch_op.create_unique_constraint(
            "uq_runs_execution_identity",
            ["audit_id", "query_id", "provider", "run_number"],
        )

    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint("fk_jobs_audit_target_id_audit_targets", type_="foreignkey")
        batch_op.drop_column("audit_target_id")
