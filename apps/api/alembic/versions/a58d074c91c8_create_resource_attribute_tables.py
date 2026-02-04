"""create resource attribute tables

Revision ID: a58d074c91c8
Revises: 12beea9c94e1
Create Date: 2026-02-04 15:33:40.669833

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a58d074c91c8"
down_revision: str | Sequence[str] | None = "12beea9c94e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create resource attribute tables.

    Implements the hybrid attribute storage strategy with type-specific tables
    for common/promoted attributes and a JSONB catch-all for rare attributes.
    """

    # resource_attrs_string - String attributes (most common type)
    op.execute("""
        CREATE TABLE resource_attrs_string (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_resource_attrs_string_value ON resource_attrs_string(key_id, value)")

    # resource_attrs_int - Integer attributes
    op.execute("""
        CREATE TABLE resource_attrs_int (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_resource_attrs_int_value ON resource_attrs_int(key_id, value)")

    # resource_attrs_double - Double precision floating point attributes
    op.execute("""
        CREATE TABLE resource_attrs_double (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_resource_attrs_double_value ON resource_attrs_double(key_id, value)")

    # resource_attrs_bool - Boolean attributes
    op.execute("""
        CREATE TABLE resource_attrs_bool (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_resource_attrs_bool_value ON resource_attrs_bool(key_id, value)")

    # resource_attrs_bytes - Binary/bytes attributes
    op.execute("""
        CREATE TABLE resource_attrs_bytes (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)

    # resource_attrs_other - JSONB catch-all for unpromoted/complex attributes
    op.execute("""
        CREATE TABLE resource_attrs_other (
            resource_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_resource_attrs_other_gin ON resource_attrs_other USING GIN(attributes)")


def downgrade() -> None:
    """Drop resource attribute tables."""
    op.execute("DROP TABLE IF EXISTS resource_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS resource_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS resource_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS resource_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS resource_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS resource_attrs_string CASCADE")
