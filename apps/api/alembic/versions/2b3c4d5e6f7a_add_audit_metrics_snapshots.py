"""Add audit metrics snapshots.

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-05-07
"""

import sqlalchemy as sa
from alembic import op

revision: str = "2b3c4d5e6f7a"
down_revision: str | None = "1a2b3c4d5e6f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "audit_metrics_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("normalized_domain", sa.String(length=255), nullable=True),
        sa.Column("normalized_brand_name", sa.String(length=255), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column(
            "audit_status",
            sa.Enum(
                "CREATED",
                "RUNNING",
                "PARTIAL",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="auditstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("audit_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("audit_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_metrics", sa.JSON(), nullable=False),
        sa.Column("model_summaries", sa.JSON(), nullable=False),
        sa.Column("source_domains_summary", sa.JSON(), nullable=False),
        sa.Column("concepts_summary", sa.JSON(), nullable=False),
        sa.Column("competitors_summary", sa.JSON(), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("scoring_version", sa.String(length=64), nullable=True),
        sa.Column("evaluation_version", sa.String(length=64), nullable=True),
        sa.Column("source_aggregation_version", sa.String(length=64), nullable=True),
        sa.Column("competitor_extractor_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("snapshot_version >= 1", name="ck_snapshot_version_positive"),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "audit_id",
            "snapshot_version",
            name="uq_audit_metrics_snapshots_audit_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_metrics_snapshots")

