"""create scope attribute tables

Revision ID: d2b90624419d
Revises: a58d074c91c8
Create Date: 2026-02-04 15:34:37.769908

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2b90624419d"
down_revision: str | Sequence[str] | None = "a58d074c91c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create scope attribute tables.

    Scope attributes track instrumentation library information.
    Uses the same hybrid storage pattern as resource attributes.
    """

    # otel_scope_attrs_string - String attributes
    op.execute("""
        CREATE TABLE otel_scope_attrs_string (
            scope_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_scope_attrs_string_value ON otel_scope_attrs_string(key_id, value)")

    # otel_scope_attrs_int - Integer attributes
    op.execute("""
        CREATE TABLE otel_scope_attrs_int (
            scope_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_scope_attrs_int_value ON otel_scope_attrs_int(key_id, value)")

    # otel_scope_attrs_double - Double precision attributes
    op.execute("""
        CREATE TABLE otel_scope_attrs_double (
            scope_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_scope_attrs_double_value ON otel_scope_attrs_double(key_id, value)")

    # otel_scope_attrs_bool - Boolean attributes
    op.execute("""
        CREATE TABLE otel_scope_attrs_bool (
            scope_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_scope_attrs_bool_value ON otel_scope_attrs_bool(key_id, value)")

    # otel_scope_attrs_bytes - Binary attributes
    op.execute("""
        CREATE TABLE otel_scope_attrs_bytes (
            scope_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )
    """)

    # otel_scope_attrs_other - JSONB catch-all
    op.execute("""
        CREATE TABLE otel_scope_attrs_other (
            scope_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_scope_attrs_other_gin ON otel_scope_attrs_other USING GIN(attributes)")


def downgrade() -> None:
    """Drop scope attribute tables."""
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_string CASCADE")
