"""create metrics data point tables

Revision ID: c838ea653e87
Revises: 60977f9e5982
Create Date: 2026-02-04 15:43:10.077341

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c838ea653e87"
down_revision: str | Sequence[str] | None = "60977f9e5982"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create metrics data point tables for all metric types.

    Implements separate tables for each data point type:
    - otel_metrics_data_points_number: For Gauge and Sum metrics
    - otel_metrics_data_points_histogram: For Histogram metrics
    - otel_metrics_data_points_exp_histogram: For ExponentialHistogram metrics
    - otel_metrics_data_points_summary: For Summary metrics
    """

    # Number data points (Gauge and Sum)
    op.execute("""
        CREATE TABLE otel_metrics_data_points_number (
            data_point_id BIGSERIAL PRIMARY KEY,

            -- Metric identification
            metric_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            start_time_unix_nano BIGINT,
            time_unix_nano BIGINT NOT NULL,

            -- Value
            value_int BIGINT,
            value_double DOUBLE PRECISION,

            -- Metadata
            flags INTEGER DEFAULT 0,
            exemplars JSONB,

            -- Ensure one value type is set
            CONSTRAINT number_value_check CHECK (
                (value_int IS NOT NULL AND value_double IS NULL) OR
                (value_int IS NULL AND value_double IS NOT NULL)
            )
        )
    """)

    # Histogram data points
    op.execute("""
        CREATE TABLE otel_metrics_data_points_histogram (
            data_point_id BIGSERIAL PRIMARY KEY,

            -- Metric identification
            metric_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            start_time_unix_nano BIGINT,
            time_unix_nano BIGINT NOT NULL,

            -- Histogram data
            count BIGINT NOT NULL,
            sum DOUBLE PRECISION,
            min DOUBLE PRECISION,
            max DOUBLE PRECISION,
            explicit_bounds DOUBLE PRECISION[],
            bucket_counts BIGINT[],

            -- Metadata
            flags INTEGER DEFAULT 0,
            exemplars JSONB
        )
    """)

    # Exponential histogram data points
    op.execute("""
        CREATE TABLE otel_metrics_data_points_exp_histogram (
            data_point_id BIGSERIAL PRIMARY KEY,

            -- Metric identification
            metric_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            start_time_unix_nano BIGINT,
            time_unix_nano BIGINT NOT NULL,

            -- Exponential histogram data
            count BIGINT NOT NULL,
            sum DOUBLE PRECISION,
            min DOUBLE PRECISION,
            max DOUBLE PRECISION,
            scale INTEGER NOT NULL,
            zero_count BIGINT NOT NULL,

            -- Positive and negative buckets
            positive_offset INTEGER,
            positive_bucket_counts BIGINT[],
            negative_offset INTEGER,
            negative_bucket_counts BIGINT[],

            -- Metadata
            flags INTEGER DEFAULT 0,
            exemplars JSONB
        )
    """)

    # Summary data points
    op.execute("""
        CREATE TABLE otel_metrics_data_points_summary (
            data_point_id BIGSERIAL PRIMARY KEY,

            -- Metric identification
            metric_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            start_time_unix_nano BIGINT,
            time_unix_nano BIGINT NOT NULL,

            -- Summary data
            count BIGINT NOT NULL,
            sum DOUBLE PRECISION NOT NULL,
            quantile_values JSONB NOT NULL,

            -- Metadata
            flags INTEGER DEFAULT 0
        )
    """)


def downgrade() -> None:
    """Drop metrics data point tables."""
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_summary CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_exp_histogram CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_histogram CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_number CASCADE")
