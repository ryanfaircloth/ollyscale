"""create spans fact table with events and links

Revision ID: 45643391e8b3
Revises: 151f87bcc9ff
Create Date: 2026-02-04 15:41:04.937475

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45643391e8b3"
down_revision: str | Sequence[str] | None = "151f87bcc9ff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create otel_spans_fact table with otel_span_events and otel_span_links child tables.

    Implements the full span data model with:
    - Main otel_spans_fact table with all OTLP span fields
    - otel_span_events for span events (normalized)
    - otel_span_links for span links (normalized)
    """

    # otel_spans_fact - Main span fact table
    op.execute("""
        CREATE TABLE otel_spans_fact (
            span_id BIGSERIAL PRIMARY KEY,

            -- Resource and scope references
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Trace identification
            trace_id VARCHAR(32) NOT NULL,
            span_id_hex VARCHAR(16) NOT NULL,
            parent_span_id_hex VARCHAR(16),
            trace_state TEXT,

            -- Span identification
            name TEXT NOT NULL,
            kind_id SMALLINT REFERENCES span_kinds(kind_id),

            -- Timing
            start_time_unix_nano BIGINT NOT NULL,
            end_time_unix_nano BIGINT NOT NULL,

            -- Status
            status_code_id SMALLINT REFERENCES status_codes(status_code_id),
            status_message TEXT,

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0,
            dropped_events_count INTEGER DEFAULT 0,
            dropped_links_count INTEGER DEFAULT 0,
            flags INTEGER DEFAULT 0
        )
    """)

    # Partition by time for efficient data lifecycle management
    # Note: Partitioning strategy will be added in a future migration

    # otel_span_events - Normalized span events
    op.execute("""
        CREATE TABLE otel_span_events (
            event_id BIGSERIAL PRIMARY KEY,
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,

            -- Event identification
            name TEXT NOT NULL,
            time_unix_nano BIGINT NOT NULL,

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0
        )
    """)

    # otel_span_links - Normalized span links
    op.execute("""
        CREATE TABLE otel_span_links (
            link_id BIGSERIAL PRIMARY KEY,
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,

            -- Linked span identification
            linked_trace_id VARCHAR(32) NOT NULL,
            linked_span_id_hex VARCHAR(16) NOT NULL,
            trace_state TEXT,

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0
        )
    """)

    # Add table and column comments
    op.execute(
        "COMMENT ON TABLE otel_spans_fact IS 'Fact table for OpenTelemetry spans with trace correlation and parent-child relationships'"
    )
    op.execute("COMMENT ON COLUMN otel_spans_fact.span_id IS 'Primary key, auto-incrementing surrogate key for span'")
    op.execute("COMMENT ON COLUMN otel_spans_fact.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.scope_id IS 'Foreign key to otel_scopes_dim (instrumentation library)'"
    )
    op.execute("COMMENT ON COLUMN otel_spans_fact.trace_id IS 'OTLP trace ID as 32-character hexadecimal string'")
    op.execute("COMMENT ON COLUMN otel_spans_fact.span_id_hex IS 'OTLP span ID as 16-character hexadecimal string'")
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.parent_span_id_hex IS 'Parent span ID as 16-character hexadecimal string, NULL for root spans'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.trace_state IS 'W3C trace state header value for context propagation'"
    )
    op.execute("COMMENT ON COLUMN otel_spans_fact.name IS 'Span operation name (e.g., GET /api/users)'")
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.kind_id IS 'Foreign key to span_kinds (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.start_time_unix_nano IS 'Span start time in nanoseconds since Unix epoch'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.end_time_unix_nano IS 'Span end time in nanoseconds since Unix epoch'"
    )
    op.execute("COMMENT ON COLUMN otel_spans_fact.status_code_id IS 'Foreign key to status_codes (UNSET, OK, ERROR)'")
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.status_message IS 'Status message, typically populated only on ERROR status'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.dropped_events_count IS 'Number of events dropped due to limits per OTLP specification'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.dropped_links_count IS 'Number of links dropped due to limits per OTLP specification'"
    )
    op.execute("COMMENT ON COLUMN otel_spans_fact.flags IS 'OTLP span flags field (bit flags for sampled, etc.)'")

    op.execute(
        "COMMENT ON TABLE otel_span_events IS 'Normalized child table for span events (e.g., exceptions, log entries within spans)'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_events.event_id IS 'Primary key, auto-incrementing surrogate key for span event'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_events.span_id IS 'Foreign key to otel_spans_fact, CASCADE delete removes events with parent span'"
    )
    op.execute("COMMENT ON COLUMN otel_span_events.name IS 'Event name (e.g., exception, http.response.start)'")
    op.execute("COMMENT ON COLUMN otel_span_events.time_unix_nano IS 'Event timestamp in nanoseconds since Unix epoch'")
    op.execute(
        "COMMENT ON COLUMN otel_span_events.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )

    op.execute(
        "COMMENT ON TABLE otel_span_links IS 'Normalized child table for span links (causal relationships to other spans)'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_links.link_id IS 'Primary key, auto-incrementing surrogate key for span link'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_links.span_id IS 'Foreign key to otel_spans_fact, CASCADE delete removes links with parent span'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_links.linked_trace_id IS 'Trace ID of the linked span as 32-character hexadecimal string'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_span_links.linked_span_id_hex IS 'Span ID of the linked span as 16-character hexadecimal string'"
    )
    op.execute("COMMENT ON COLUMN otel_span_links.trace_state IS 'W3C trace state for the linked span'")
    op.execute(
        "COMMENT ON COLUMN otel_span_links.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )


def downgrade() -> None:
    """Drop otel_spans_fact and related tables."""
    op.execute("DROP TABLE IF EXISTS otel_span_links CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_events CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_spans_fact CASCADE")
