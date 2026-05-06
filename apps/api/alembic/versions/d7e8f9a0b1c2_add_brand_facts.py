"""add brand facts

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-05-06 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "c6d7e8f9a0b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column(
            "fact_type",
            sa.Enum(
                "brand_name",
                "official_domain",
                "description_claim",
                "user_provided",
                "domain_analysis_future",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "brand_name",
                "brand_domain",
                "brand_description",
                "user",
                "system",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "fact_type IN ('brand_name', 'official_domain', 'description_claim', "
            "'user_provided', 'domain_analysis_future')",
            name="ck_brand_facts_fact_type",
        ),
        sa.CheckConstraint(
            "source IN ('brand_name', 'brand_domain', 'brand_description', "
            "'user', 'system')",
            name="ck_brand_facts_source",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_brand_facts_confidence_range",
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("brand_facts")
