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


def downgrade() -> None:
    """Drop otel_resources_dim and otel_scopes_dim dimension tables."""
    op.execute("DROP TABLE IF EXISTS otel_scopes_dim CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resources_dim CASCADE")
