"""create resources and scopes dimension tables

Revision ID: 3cd27c4cad39
Revises: a69cb863cc37
Create Date: 2026-02-04 15:39:39.713648

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3cd27c4cad39"
down_revision: str | Sequence[str] | None = "a69cb863cc37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create otel_resources_dim and otel_scopes_dim dimension tables.

    These tables implement hash-based deduplication with temporal tracking.
    The resource_hash ensures uniqueness while first_seen/last_seen track
    the temporal range for each unique resource/scope configuration.
    """

    # otel_resources_dim - Resource deduplication with hash-based identity
    op.execute("""
        CREATE TABLE otel_resources_dim (
            resource_id BIGSERIAL PRIMARY KEY,
            resource_hash VARCHAR(64) NOT NULL UNIQUE,

            -- Extracted well-known fields for fast access
            service_name TEXT,
            service_namespace TEXT,

            -- Schema versioning
            schema_url TEXT,

            -- Temporal tracking (critical for deduplication)
            first_seen TIMESTAMPTZ DEFAULT NOW(),
            last_seen TIMESTAMPTZ DEFAULT NOW(),

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0
        )
    """)

    # Indexes for common query patterns
    op.execute("CREATE INDEX idx_otel_resources_dim_service_name ON otel_resources_dim(service_name)")
    op.execute("CREATE INDEX idx_otel_resources_dim_namespace ON otel_resources_dim(service_namespace)")
    op.execute("CREATE INDEX idx_otel_resources_dim_last_seen ON otel_resources_dim(last_seen)")

    # otel_scopes_dim - Scope (instrumentation library) deduplication
    op.execute("""
        CREATE TABLE otel_scopes_dim (
            scope_id BIGSERIAL PRIMARY KEY,
            scope_hash VARCHAR(64) NOT NULL UNIQUE,

            -- Scope identification
            name TEXT,
            version TEXT,

            -- Schema versioning
            schema_url TEXT,

            -- Temporal tracking
            first_seen TIMESTAMPTZ DEFAULT NOW(),
            last_seen TIMESTAMPTZ DEFAULT NOW(),

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0
        )
    """)

    # Indexes for scope lookups
    op.execute("CREATE INDEX idx_otel_scopes_dim_name ON otel_scopes_dim(name)")
    op.execute("CREATE INDEX idx_otel_scopes_dim_last_seen ON otel_scopes_dim(last_seen)")

    # Add table and column comments for otel_resources_dim
    op.execute(
        "COMMENT ON TABLE otel_resources_dim IS 'Dimension table for OpenTelemetry resource deduplication with hash-based identity and temporal tracking'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.resource_id IS 'Primary key, auto-incrementing surrogate key for resource dimension'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.resource_hash IS 'SHA-256 hash of resource attributes, ensures uniqueness'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.service_name IS 'Extracted service.name attribute for fast filtering'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.service_namespace IS 'Extracted service.namespace attribute for fast filtering'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.schema_url IS 'OTLP schema URL for semantic convention versioning'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.first_seen IS 'Timestamp when this resource configuration was first observed'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.last_seen IS 'Timestamp when this resource configuration was last observed, updated on ingestion'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )

    # Add table and column comments for otel_scopes_dim
    op.execute(
        "COMMENT ON TABLE otel_scopes_dim IS 'Dimension table for OpenTelemetry instrumentation scope (library) deduplication with hash-based identity'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_scopes_dim.scope_id IS 'Primary key, auto-incrementing surrogate key for scope dimension'"
    )
    op.execute("COMMENT ON COLUMN otel_scopes_dim.scope_hash IS 'SHA-256 hash of scope attributes, ensures uniqueness'")
    op.execute("COMMENT ON COLUMN otel_scopes_dim.name IS 'Instrumentation library name (e.g., io.opentelemetry.jdbc)'")
    op.execute("COMMENT ON COLUMN otel_scopes_dim.version IS 'Instrumentation library version'")
    op.execute("COMMENT ON COLUMN otel_scopes_dim.schema_url IS 'OTLP schema URL for semantic convention versioning'")
    op.execute(
        "COMMENT ON COLUMN otel_scopes_dim.first_seen IS 'Timestamp when this scope configuration was first observed'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_scopes_dim.last_seen IS 'Timestamp when this scope configuration was last observed, updated on ingestion'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_scopes_dim.dropped_attributes_count IS 'Number of attributes dropped due to limits per OTLP specification'"
    )


def downgrade() -> None:
    """Drop otel_resources_dim and otel_scopes_dim dimension tables."""
    op.execute("DROP TABLE IF EXISTS otel_scopes_dim CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resources_dim CASCADE")
