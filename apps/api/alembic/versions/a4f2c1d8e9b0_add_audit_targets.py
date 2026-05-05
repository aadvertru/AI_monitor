"""add audit targets

Revision ID: a4f2c1d8e9b0
Revises: 9d1e2f3a4b5c
Create Date: 2026-05-05 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4f2c1d8e9b0"
down_revision: str | None = "9d1e2f3a4b5c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("ai_family", sa.String(length=64), nullable=False),
        sa.Column("execution_provider", sa.String(length=64), nullable=False),
        sa.Column("model_provider", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=2), nullable=False),
        sa.Column("gateway", sa.Boolean(), nullable=False),
        sa.Column("gateway_l2_experimental", sa.Boolean(), nullable=False),
        sa.Column("provider_config_snapshot", sa.JSON(), nullable=True),
        sa.Column("model_display_order", sa.Integer(), nullable=True),
        sa.Column("capability_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("level IN ('L1', 'L2')", name="ck_audit_targets_level"),
        sa.CheckConstraint(
            "NOT (gateway_l2_experimental AND level = 'L1')",
            name="ck_audit_targets_l2_gateway_only",
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_targets")
