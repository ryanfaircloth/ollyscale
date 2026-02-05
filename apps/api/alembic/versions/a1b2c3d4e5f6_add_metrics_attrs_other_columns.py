"""add attributes_other columns to metrics data points

Revision ID: a1b2c3d4e5f6
Revises: f2a3b4c5d6e7
Create Date: 2026-02-04 18:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add attributes_other JSONB columns to all metrics data point tables.

    This column stores non-promoted metric data point attributes as a catch-all,
    ensuring no data loss while keeping promoted attributes in typed tables
    for efficient querying (future enhancement).
    """

    # Add attributes_other to number data points (Gauge and Sum)
    op.execute("""
        ALTER TABLE otel_metrics_data_points_number
        ADD COLUMN attributes_other JSONB DEFAULT NULL
    """)

    op.execute("""
        COMMENT ON COLUMN otel_metrics_data_points_number.attributes_other IS
        'JSONB catch-all for data point attributes. Future: promoted attributes
         will be stored in typed tables for efficient querying.'
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_dp_number_attrs_gin
        ON otel_metrics_data_points_number USING GIN (attributes_other)
        WHERE attributes_other IS NOT NULL
    """)

    # Add attributes_other to histogram data points
    op.execute("""
        ALTER TABLE otel_metrics_data_points_histogram
        ADD COLUMN attributes_other JSONB DEFAULT NULL
    """)

    op.execute("""
        COMMENT ON COLUMN otel_metrics_data_points_histogram.attributes_other IS
        'JSONB catch-all for data point attributes. Future: promoted attributes
         will be stored in typed tables for efficient querying.'
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_dp_histogram_attrs_gin
        ON otel_metrics_data_points_histogram USING GIN (attributes_other)
        WHERE attributes_other IS NOT NULL
    """)

    # Add attributes_other to exponential histogram data points
    op.execute("""
        ALTER TABLE otel_metrics_data_points_exp_histogram
        ADD COLUMN attributes_other JSONB DEFAULT NULL
    """)

    op.execute("""
        COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.attributes_other IS
        'JSONB catch-all for data point attributes. Future: promoted attributes
         will be stored in typed tables for efficient querying.'
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_dp_exp_histogram_attrs_gin
        ON otel_metrics_data_points_exp_histogram USING GIN (attributes_other)
        WHERE attributes_other IS NOT NULL
    """)

    # Add attributes_other to summary data points
    op.execute("""
        ALTER TABLE otel_metrics_data_points_summary
        ADD COLUMN attributes_other JSONB DEFAULT NULL
    """)

    op.execute("""
        COMMENT ON COLUMN otel_metrics_data_points_summary.attributes_other IS
        'JSONB catch-all for data point attributes. Future: promoted attributes
         will be stored in typed tables for efficient querying.'
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_dp_summary_attrs_gin
        ON otel_metrics_data_points_summary USING GIN (attributes_other)
        WHERE attributes_other IS NOT NULL
    """)


def downgrade() -> None:
    """Remove attributes_other columns from all metrics data point tables."""
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_dp_summary_attrs_gin")
    op.execute("ALTER TABLE otel_metrics_data_points_summary DROP COLUMN IF EXISTS attributes_other")

    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_dp_exp_histogram_attrs_gin")
    op.execute("ALTER TABLE otel_metrics_data_points_exp_histogram DROP COLUMN IF EXISTS attributes_other")

    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_dp_histogram_attrs_gin")
    op.execute("ALTER TABLE otel_metrics_data_points_histogram DROP COLUMN IF EXISTS attributes_other")

    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_dp_number_attrs_gin")
    op.execute("ALTER TABLE otel_metrics_data_points_number DROP COLUMN IF EXISTS attributes_other")
