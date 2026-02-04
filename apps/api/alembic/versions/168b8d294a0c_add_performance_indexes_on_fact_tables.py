"""add performance indexes on fact tables

Revision ID: 168b8d294a0c
Revises: c838ea653e87
Create Date: 2026-02-04 15:43:33.337506

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "168b8d294a0c"
down_revision: str | Sequence[str] | None = "c838ea653e87"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes on fact tables for common query patterns.

    Indexes organized by table and query pattern:
    - Trace queries (trace_id, span lookups)
    - Time range queries (start_time, time)
    - Resource filtering (resource_id)
    - Severity filtering (severity_number_id)
    - Metric queries (metric_id)
    - Correlation lookups (trace correlation, span links)
    """

    # ========== SPANS_FACT INDEXES ==========

    # Trace queries - most common access pattern
    op.execute("""
        CREATE INDEX idx_otel_spans_trace_id
        ON otel_spans_fact(trace_id)
    """)

    # Exact span lookup
    op.execute("""
        CREATE INDEX idx_otel_spans_trace_span_id
        ON otel_spans_fact(trace_id, span_id_hex)
    """)

    # Parent-child relationships for trace tree building
    op.execute("""
        CREATE INDEX idx_otel_spans_parent_span_id
        ON otel_spans_fact(parent_span_id_hex)
        WHERE parent_span_id_hex IS NOT NULL
    """)

    # Time range queries
    op.execute("""
        CREATE INDEX idx_otel_spans_start_time
        ON otel_spans_fact(start_time_unix_nano DESC)
    """)

    # Resource filtering
    op.execute("""
        CREATE INDEX idx_otel_spans_resource_id
        ON otel_spans_fact(resource_id)
    """)

    # Operation name filtering
    op.execute("""
        CREATE INDEX idx_otel_spans_name
        ON otel_spans_fact(name)
    """)

    # Composite for common filtered queries
    op.execute("""
        CREATE INDEX idx_otel_spans_resource_time
        ON otel_spans_fact(resource_id, start_time_unix_nano DESC)
    """)

    # ========== SPAN_EVENTS INDEXES ==========

    # Span relationship (FK already indexed, but explicit for clarity)
    op.execute("""
        CREATE INDEX idx_otel_span_events_span_id
        ON otel_span_events(span_id)
    """)

    # Event time ordering
    op.execute("""
        CREATE INDEX idx_otel_span_events_time
        ON otel_span_events(time_unix_nano)
    """)

    # ========== SPAN_LINKS INDEXES ==========

    # Span relationship
    op.execute("""
        CREATE INDEX idx_otel_span_links_span_id
        ON otel_span_links(span_id)
    """)

    # Backtrace from linked trace
    op.execute("""
        CREATE INDEX idx_otel_span_links_linked_trace
        ON otel_span_links(linked_trace_id, linked_span_id_hex)
    """)

    # ========== LOGS_FACT INDEXES ==========

    # Time range queries - primary access pattern
    op.execute("""
        CREATE INDEX idx_otel_logs_time
        ON otel_logs_fact(time_unix_nano DESC)
    """)

    # Resource filtering
    op.execute("""
        CREATE INDEX idx_otel_logs_resource_id
        ON otel_logs_fact(resource_id)
    """)

    # Severity filtering
    op.execute("""
        CREATE INDEX idx_otel_logs_severity
        ON otel_logs_fact(severity_number)
        WHERE severity_number IS NOT NULL
    """)

    # Trace correlation
    op.execute("""
        CREATE INDEX idx_otel_logs_trace_correlation
        ON otel_logs_fact(trace_id, span_id_hex)
        WHERE trace_id IS NOT NULL
    """)

    # Composite for common filtered queries
    op.execute("""
        CREATE INDEX idx_otel_logs_resource_time
        ON otel_logs_fact(resource_id, time_unix_nano DESC)
    """)

    # ========== METRICS DATA POINTS INDEXES ==========

    # Number data points
    op.execute("""
        CREATE INDEX idx_otel_metrics_number_metric_id
        ON otel_metrics_data_points_number(metric_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_number_resource_id
        ON otel_metrics_data_points_number(resource_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_number_time
        ON otel_metrics_data_points_number(time_unix_nano DESC)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_number_metric_time
        ON otel_metrics_data_points_number(metric_id, time_unix_nano DESC)
    """)

    # Histogram data points
    op.execute("""
        CREATE INDEX idx_otel_metrics_histogram_metric_id
        ON otel_metrics_data_points_histogram(metric_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_histogram_resource_id
        ON otel_metrics_data_points_histogram(resource_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_histogram_time
        ON otel_metrics_data_points_histogram(time_unix_nano DESC)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_histogram_metric_time
        ON otel_metrics_data_points_histogram(metric_id, time_unix_nano DESC)
    """)

    # Exponential histogram data points
    op.execute("""
        CREATE INDEX idx_otel_metrics_exp_histogram_metric_id
        ON otel_metrics_data_points_exp_histogram(metric_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_exp_histogram_resource_id
        ON otel_metrics_data_points_exp_histogram(resource_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_exp_histogram_time
        ON otel_metrics_data_points_exp_histogram(time_unix_nano DESC)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_exp_histogram_metric_time
        ON otel_metrics_data_points_exp_histogram(metric_id, time_unix_nano DESC)
    """)

    # Summary data points
    op.execute("""
        CREATE INDEX idx_otel_metrics_summary_metric_id
        ON otel_metrics_data_points_summary(metric_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_summary_resource_id
        ON otel_metrics_data_points_summary(resource_id)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_summary_time
        ON otel_metrics_data_points_summary(time_unix_nano DESC)
    """)

    op.execute("""
        CREATE INDEX idx_otel_metrics_summary_metric_time
        ON otel_metrics_data_points_summary(metric_id, time_unix_nano DESC)
    """)


def downgrade() -> None:
    """Drop performance indexes."""

    # Spans
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_resource_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_name")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_start_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_parent_span_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_trace_span_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_spans_trace_id")

    # Span events
    op.execute("DROP INDEX IF EXISTS idx_otel_span_events_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_span_events_span_id")

    # Span links
    op.execute("DROP INDEX IF EXISTS idx_otel_span_links_linked_trace")
    op.execute("DROP INDEX IF EXISTS idx_otel_span_links_span_id")

    # Logs
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_resource_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_trace_correlation")
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_severity")
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_logs_time")

    # Metrics - Number
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_number_metric_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_number_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_number_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_number_metric_id")

    # Metrics - Histogram
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_histogram_metric_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_histogram_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_histogram_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_histogram_metric_id")

    # Metrics - Exponential Histogram
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_exp_histogram_metric_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_exp_histogram_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_exp_histogram_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_exp_histogram_metric_id")

    # Metrics - Summary
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_summary_metric_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_summary_time")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_summary_resource_id")
    op.execute("DROP INDEX IF EXISTS idx_otel_metrics_summary_metric_id")
