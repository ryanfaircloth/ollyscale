"""create resources and scopes dimension tables

Revision ID: 3cd27c4cad39
Revises: a69cb863cc37
Create Date: 2026-02-04 15:39:39.713648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cd27c4cad39'
down_revision: Union[str, Sequence[str], None] = 'a69cb863cc37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create resources_dim and scopes_dim dimension tables.

    These tables implement hash-based deduplication with temporal tracking.
    The resource_hash ensures uniqueness while first_seen/last_seen track
    the temporal range for each unique resource/scope configuration.
    """

    # resources_dim - Resource deduplication with hash-based identity
    op.execute("""
        CREATE TABLE resources_dim (
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
    op.execute(
        "CREATE INDEX idx_resources_dim_service_name ON resources_dim(service_name)"
    )
    op.execute(
        "CREATE INDEX idx_resources_dim_namespace ON resources_dim(service_namespace)"
    )
    op.execute(
        "CREATE INDEX idx_resources_dim_last_seen ON resources_dim(last_seen)"
    )

    # scopes_dim - Scope (instrumentation library) deduplication
    op.execute("""
        CREATE TABLE scopes_dim (
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
    op.execute("CREATE INDEX idx_scopes_dim_name ON scopes_dim(name)")
    op.execute("CREATE INDEX idx_scopes_dim_last_seen ON scopes_dim(last_seen)")


def downgrade() -> None:
    """Drop resources_dim and scopes_dim dimension tables."""
    op.execute("DROP TABLE IF EXISTS scopes_dim CASCADE")
    op.execute("DROP TABLE IF EXISTS resources_dim CASCADE")
