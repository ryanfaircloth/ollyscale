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

    # otel_resource_attrs_string - String attributes (most common type)
    op.execute("""
        CREATE TABLE otel_resource_attrs_string (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_resource_attrs_string_value ON otel_resource_attrs_string(key_id, value)")

    # otel_resource_attrs_int - Integer attributes
    op.execute("""
        CREATE TABLE otel_resource_attrs_int (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_resource_attrs_int_value ON otel_resource_attrs_int(key_id, value)")

    # otel_resource_attrs_double - Double precision floating point attributes
    op.execute("""
        CREATE TABLE otel_resource_attrs_double (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_resource_attrs_double_value ON otel_resource_attrs_double(key_id, value)")

    # otel_resource_attrs_bool - Boolean attributes
    op.execute("""
        CREATE TABLE otel_resource_attrs_bool (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_resource_attrs_bool_value ON otel_resource_attrs_bool(key_id, value)")

    # otel_resource_attrs_bytes - Binary/bytes attributes
    op.execute("""
        CREATE TABLE otel_resource_attrs_bytes (
            resource_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )
    """)

    # otel_resource_attrs_other - JSONB catch-all for unpromoted/complex attributes
    op.execute("""
        CREATE TABLE otel_resource_attrs_other (
            resource_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_resource_attrs_other_gin ON otel_resource_attrs_other USING GIN(attributes)")

    # Add table and column comments
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_string IS 'String-typed resource attributes stored in dedicated table for query performance'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_string.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_string.key_id IS 'Foreign key to attribute_keys for attribute name'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_string.value IS 'String attribute value'")

    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_int IS 'Integer-typed resource attributes stored in dedicated table for query performance'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_int.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute("COMMENT ON COLUMN otel_resource_attrs_int.key_id IS 'Foreign key to attribute_keys for attribute name'")
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_int.value IS 'Integer attribute value (BIGINT for full range support)'"
    )

    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_double IS 'Double precision floating point resource attributes stored in dedicated table for query performance'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_double.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_double.key_id IS 'Foreign key to attribute_keys for attribute name'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_double.value IS 'Double precision floating point attribute value'"
    )

    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_bool IS 'Boolean-typed resource attributes stored in dedicated table for query performance'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_bool.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_bool.key_id IS 'Foreign key to attribute_keys for attribute name'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_bool.value IS 'Boolean attribute value'")

    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_bytes IS 'Binary/bytes resource attributes stored in dedicated table'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_bytes.resource_id IS 'Foreign key to otel_resources_dim'")
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_bytes.key_id IS 'Foreign key to attribute_keys for attribute name'"
    )
    op.execute("COMMENT ON COLUMN otel_resource_attrs_bytes.value IS 'Binary attribute value stored as BYTEA'")

    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_other IS 'JSONB catch-all for unpromoted, complex, or array-typed resource attributes'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_other.resource_id IS 'Primary key and foreign key to otel_resources_dim'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_resource_attrs_other.attributes IS 'JSONB object containing all unpromoted attributes for this resource'"
    )


def downgrade() -> None:
    """Drop resource attribute tables."""
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_string CASCADE")
