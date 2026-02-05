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

    # Add table and column comments for all data point tables
    op.execute(
        "COMMENT ON TABLE otel_metrics_data_points_number IS 'Fact table for Gauge and Sum metric data points with integer or double precision values'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.data_point_id IS 'Primary key, auto-incrementing surrogate key for data point'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_number.metric_id IS 'Foreign key to otel_metrics_dim'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_number.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_number.scope_id IS 'Foreign key to otel_scopes_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.start_time_unix_nano IS 'Start time for cumulative metrics in nanoseconds since Unix epoch, NULL for gauges'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.time_unix_nano IS 'Data point timestamp in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.value_int IS 'Integer metric value, mutually exclusive with value_double'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.value_double IS 'Double precision metric value, mutually exclusive with value_int'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_number.flags IS 'OTLP data point flags field'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_number.exemplars IS 'JSONB array of exemplars (sample traces for this metric value)'"
    )

    op.execute(
        "COMMENT ON TABLE otel_metrics_data_points_histogram IS 'Fact table for Histogram metric data points with explicit bucket boundaries'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.data_point_id IS 'Primary key, auto-incrementing surrogate key for data point'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.metric_id IS 'Foreign key to otel_metrics_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.resource_id IS 'Foreign key to otel_resources_dim'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.scope_id IS 'Foreign key to otel_scopes_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.start_time_unix_nano IS 'Start time for cumulative histograms in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.time_unix_nano IS 'Data point timestamp in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.count IS 'Total count of observations in histogram'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.sum IS 'Sum of all observed values, optional'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.min IS 'Minimum observed value, optional'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.max IS 'Maximum observed value, optional'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.explicit_bounds IS 'Array of bucket boundary values in ascending order'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.bucket_counts IS 'Array of counts for each bucket, length is len(explicit_bounds) + 1'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_histogram.flags IS 'OTLP data point flags field'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_histogram.exemplars IS 'JSONB array of exemplars for histogram buckets'"
    )

    op.execute(
        "COMMENT ON TABLE otel_metrics_data_points_exp_histogram IS 'Fact table for ExponentialHistogram metric data points with exponentially-sized buckets'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.data_point_id IS 'Primary key, auto-incrementing surrogate key for data point'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.metric_id IS 'Foreign key to otel_metrics_dim'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.resource_id IS 'Foreign key to otel_resources_dim'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.scope_id IS 'Foreign key to otel_scopes_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.start_time_unix_nano IS 'Start time for cumulative histograms in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.time_unix_nano IS 'Data point timestamp in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.count IS 'Total count of observations in exponential histogram'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.sum IS 'Sum of all observed values, optional'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.min IS 'Minimum observed value, optional'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.max IS 'Maximum observed value, optional'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.scale IS 'Exponential histogram scale parameter, determines bucket width'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.zero_count IS 'Count of observations exactly equal to zero'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.positive_offset IS 'Offset for positive bucket indexing'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.positive_bucket_counts IS 'Array of counts for positive value buckets'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.negative_offset IS 'Offset for negative bucket indexing'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.negative_bucket_counts IS 'Array of counts for negative value buckets'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.flags IS 'OTLP data point flags field'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_exp_histogram.exemplars IS 'JSONB array of exemplars for histogram buckets'"
    )

    op.execute(
        "COMMENT ON TABLE otel_metrics_data_points_summary IS 'Fact table for Summary metric data points with pre-computed quantiles'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_summary.data_point_id IS 'Primary key, auto-incrementing surrogate key for data point'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.metric_id IS 'Foreign key to otel_metrics_dim'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.scope_id IS 'Foreign key to otel_scopes_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_summary.start_time_unix_nano IS 'Start time for summary calculation window in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_summary.time_unix_nano IS 'Data point timestamp in nanoseconds since Unix epoch'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.count IS 'Total count of observations in summary'")
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.sum IS 'Sum of all observed values'")
    op.execute(
        "COMMENT ON COLUMN otel_metrics_data_points_summary.quantile_values IS 'JSONB array of quantile/value pairs (e.g., [{quantile: 0.5, value: 123}, {quantile: 0.99, value: 456}])'"
    )
    op.execute("COMMENT ON COLUMN otel_metrics_data_points_summary.flags IS 'OTLP data point flags field'")


def downgrade() -> None:
    """Drop metrics data point tables."""
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_summary CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_exp_histogram CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_histogram CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_metrics_data_points_number CASCADE")
