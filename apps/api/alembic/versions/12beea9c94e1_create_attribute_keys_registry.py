"""create attribute keys registry

Revision ID: 12beea9c94e1
Revises: cc126c4310c0
Create Date: 2026-02-04 15:29:48.132013

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12beea9c94e1"
down_revision: str | Sequence[str] | None = "cc126c4310c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create attribute_keys registry table.

    This table serves as the central registry for all attribute keys used across
    the system. It enables:
    - Type-aware attribute storage (string, int, double, bool, bytes)
    - Control over which attributes are indexed and searchable
    - Efficient storage by using integer key_ids instead of repeating key names
    """
    op.execute("""
        CREATE TABLE attribute_keys (
            key_id SERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            description TEXT,
            value_type TEXT NOT NULL CHECK (value_type IN ('string', 'int', 'double', 'bool', 'bytes')),
            is_indexed BOOLEAN DEFAULT false,
            is_searchable BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create index for lookups by key name
    op.execute("CREATE INDEX idx_attribute_keys_key ON attribute_keys(key)")

    # Seed with common OTEL semantic convention attributes
    op.execute("""
        INSERT INTO attribute_keys (key, value_type, is_indexed, is_searchable) VALUES
            -- Resource attributes (service identity)
            ('service.name', 'string', true, true),
            ('service.namespace', 'string', true, true),
            ('service.version', 'string', true, true),
            ('service.instance.id', 'string', true, true),
            ('deployment.environment', 'string', true, true),

            -- K8s resource attributes
            ('k8s.cluster.name', 'string', true, true),
            ('k8s.namespace.name', 'string', true, true),
            ('k8s.deployment.name', 'string', true, true),
            ('k8s.pod.name', 'string', true, false),
            ('k8s.container.name', 'string', true, true),

            -- SDK attributes
            ('telemetry.sdk.name', 'string', false, false),
            ('telemetry.sdk.language', 'string', false, false),
            ('telemetry.sdk.version', 'string', false, false),

            -- Common span attributes
            ('http.method', 'string', true, true),
            ('http.status_code', 'int', true, true),
            ('http.url', 'string', false, true),
            ('http.target', 'string', false, true),
            ('db.system', 'string', true, true),
            ('db.name', 'string', true, true),
            ('db.operation', 'string', true, true),
            ('error', 'bool', true, true),
            ('error.type', 'string', true, true)
    """)


def downgrade() -> None:
    """Drop attribute_keys registry table."""
    op.execute("DROP TABLE IF EXISTS attribute_keys CASCADE")
