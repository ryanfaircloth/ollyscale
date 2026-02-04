"""create span attribute tables

Revision ID: 78d5e132a70b
Revises: 3cd27c4cad39
Create Date: 2026-02-04 15:40:06.794261

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "78d5e132a70b"
down_revision: str | Sequence[str] | None = "3cd27c4cad39"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create span, span_event, and span_link attribute tables.

    Uses the hybrid storage pattern for all three contexts:
    - Span attributes
    - Span event attributes
    - Span link attributes
    """

    # ============ SPAN ATTRIBUTES ============

    # otel_span_attrs_string
    op.execute("""
        CREATE TABLE otel_span_attrs_string (
            span_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_attrs_string_value ON otel_span_attrs_string(key_id, value)")

    # otel_span_attrs_int
    op.execute("""
        CREATE TABLE otel_span_attrs_int (
            span_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_attrs_int_value ON otel_span_attrs_int(key_id, value)")

    # otel_span_attrs_double
    op.execute("""
        CREATE TABLE otel_span_attrs_double (
            span_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )
    """)

    # otel_span_attrs_bool
    op.execute("""
        CREATE TABLE otel_span_attrs_bool (
            span_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )
    """)

    # otel_span_attrs_bytes
    op.execute("""
        CREATE TABLE otel_span_attrs_bytes (
            span_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )
    """)

    # otel_span_attrs_other
    op.execute("""
        CREATE TABLE otel_span_attrs_other (
            span_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_attrs_other_gin ON otel_span_attrs_other USING GIN(attributes)")

    # ============ SPAN EVENT ATTRIBUTES ============

    # otel_span_event_attrs_string
    op.execute("""
        CREATE TABLE otel_span_event_attrs_string (
            event_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (event_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_event_attrs_string_value ON otel_span_event_attrs_string(key_id, value)")

    # otel_span_event_attrs_int
    op.execute("""
        CREATE TABLE otel_span_event_attrs_int (
            event_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (event_id, key_id)
        )
    """)

    # otel_span_event_attrs_double
    op.execute("""
        CREATE TABLE otel_span_event_attrs_double (
            event_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (event_id, key_id)
        )
    """)

    # otel_span_event_attrs_bool
    op.execute("""
        CREATE TABLE otel_span_event_attrs_bool (
            event_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (event_id, key_id)
        )
    """)

    # otel_span_event_attrs_bytes
    op.execute("""
        CREATE TABLE otel_span_event_attrs_bytes (
            event_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (event_id, key_id)
        )
    """)

    # otel_span_event_attrs_other
    op.execute("""
        CREATE TABLE otel_span_event_attrs_other (
            event_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_event_attrs_other_gin ON otel_span_event_attrs_other USING GIN(attributes)")

    # ============ SPAN LINK ATTRIBUTES ============

    # otel_span_link_attrs_string
    op.execute("""
        CREATE TABLE otel_span_link_attrs_string (
            link_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (link_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_link_attrs_string_value ON otel_span_link_attrs_string(key_id, value)")

    # otel_span_link_attrs_int
    op.execute("""
        CREATE TABLE otel_span_link_attrs_int (
            link_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (link_id, key_id)
        )
    """)

    # otel_span_link_attrs_double
    op.execute("""
        CREATE TABLE otel_span_link_attrs_double (
            link_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (link_id, key_id)
        )
    """)

    # otel_span_link_attrs_bool
    op.execute("""
        CREATE TABLE otel_span_link_attrs_bool (
            link_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (link_id, key_id)
        )
    """)

    # otel_span_link_attrs_bytes
    op.execute("""
        CREATE TABLE otel_span_link_attrs_bytes (
            link_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (link_id, key_id)
        )
    """)

    # otel_span_link_attrs_other
    op.execute("""
        CREATE TABLE otel_span_link_attrs_other (
            link_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_span_link_attrs_other_gin ON otel_span_link_attrs_other USING GIN(attributes)")


def downgrade() -> None:
    """Drop span attribute tables."""
    # Span link attrs
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_link_attrs_string CASCADE")

    # Span event attrs
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_event_attrs_string CASCADE")

    # Span attrs
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_string CASCADE")
