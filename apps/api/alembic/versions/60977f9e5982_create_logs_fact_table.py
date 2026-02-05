"""create logs fact table

Revision ID: 60977f9e5982
Revises: 45643391e8b3
Create Date: 2026-02-04 15:42:52.073881

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60977f9e5982"
down_revision: str | Sequence[str] | None = "45643391e8b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create otel_logs_fact table.

    Implements the log record data model with:
    - All OTLP log record fields
    - References to dimension tables
    - Optional trace correlation fields
    """

    op.execute("""
        CREATE TABLE otel_logs_fact (
            log_id BIGSERIAL PRIMARY KEY,

            -- Resource and scope references
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            time_unix_nano BIGINT NOT NULL,
            observed_time_unix_nano BIGINT NOT NULL,

            -- Severity
            severity_number SMALLINT REFERENCES log_severity_numbers(severity_number),
            severity_text TEXT,

            -- Body
            body_type_id SMALLINT REFERENCES log_body_types(body_type_id),
            body JSONB,

            -- Trace correlation (optional fields)
            trace_id VARCHAR(32),
            span_id_hex VARCHAR(16),
            trace_flags INTEGER,

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0,
            flags INTEGER DEFAULT 0
        )
    """)

    # Partition by time for efficient data lifecycle management
    # Note: Partitioning strategy will be added in a future migration

    # Add table and column comments
    op.execute(
        "COMMENT ON TABLE otel_logs_fact IS 'Fact table for OpenTelemetry log records with optional trace correlation'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.log_id IS 'Primary key, auto-incrementing surrogate key for log record'"
    )
    op.execute("COMMENT ON COLUMN otel_logs_fact.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.scope_id IS 'Foreign key to otel_scopes_dim (instrumentation library)'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.time_unix_nano IS 'Log record timestamp in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.observed_time_unix_nano IS 'Timestamp when log was observed by collection system in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.severity_number IS 'Foreign key to log_severity_numbers (1-24 range per OTLP spec)'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.severity_text IS 'Severity text (e.g., INFO, ERROR, DEBUG), can be arbitrary string'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.body_type_id IS 'Foreign key to log_body_types indicating body value type'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.body IS 'JSONB log body content, can be string, number, boolean, or structured object'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.trace_id IS 'Optional trace correlation: trace ID as 32-character hexadecimal string'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.span_id_hex IS 'Optional trace correlation: span ID as 16-character hexadecimal string'"
    )
    op.execute("COMMENT ON COLUMN otel_logs_fact.trace_flags IS 'Optional trace correlation: OTLP trace flags field'")
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )
    op.execute("COMMENT ON COLUMN otel_logs_fact.flags IS 'OTLP log record flags field'")


def downgrade() -> None:
    """Drop otel_logs_fact table."""
    op.execute("DROP TABLE IF EXISTS otel_logs_fact CASCADE")
