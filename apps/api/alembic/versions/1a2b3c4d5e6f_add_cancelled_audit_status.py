"""Add cancelled audit status.

Revision ID: 1a2b3c4d5e6f
Revises: 0a1b2c3d4e5f
Create Date: 2026-05-07
"""

from alembic import op

revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "0a1b2c3d4e5f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """No-op for native_enum=False storage.

    Audit status is stored as a string column in the current schema. This
    revision records the public contract change for deployments that stamp and
    track schema versions.
    """


def downgrade() -> None:
    op.execute("UPDATE audits SET status = 'FAILED' WHERE status = 'CANCELLED'")
    op.execute("UPDATE audits SET status = 'failed' WHERE status = 'cancelled'")
