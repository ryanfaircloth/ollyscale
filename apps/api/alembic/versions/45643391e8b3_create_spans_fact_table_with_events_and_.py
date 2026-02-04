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


def downgrade() -> None:
    """Drop otel_spans_fact and related tables."""
    op.execute("DROP TABLE IF EXISTS otel_span_links CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_events CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_spans_fact CASCADE")
