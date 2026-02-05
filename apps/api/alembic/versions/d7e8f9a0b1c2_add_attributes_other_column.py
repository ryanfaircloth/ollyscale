"""add attributes_other column to logs fact

Revision ID: d7e8f9a0b1c2
Revises: 168b8d294a0c
Create Date: 2026-02-04 16:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: str | Sequence[str] | None = "168b8d294a0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add attributes_other JSONB column to otel_logs_fact.

    This column stores non-promoted attributes as a catch-all, ensuring
    no data loss while keeping promoted attributes in typed tables for
    efficient querying.
    """

    op.execute("""
        ALTER TABLE otel_logs_fact
        ADD COLUMN attributes_other JSONB DEFAULT NULL
    """)

    # Add column comment
    op.execute("""
        COMMENT ON COLUMN otel_logs_fact.attributes_other IS
        'JSONB catch-all for non-promoted log attributes. Promoted attributes
         are stored in typed otel_log_attrs_* tables for efficient querying.
         This ensures no data loss while optimizing common query patterns.'
    """)

    # Add GIN index for JSONB operators (@>, ?, etc.)
    op.execute("""
        CREATE INDEX idx_otel_logs_attrs_other_gin
        ON otel_logs_fact USING GIN (attributes_other)
        WHERE attributes_other IS NOT NULL
    """)


def downgrade() -> None:
    """Remove attributes_other column."""
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_attrs_other_gin")
    op.execute("ALTER TABLE otel_logs_fact DROP COLUMN IF EXISTS attributes_other")
