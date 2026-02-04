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

    # Add table and column comments for all attribute tables
    op.execute("""
        -- Span attributes
        COMMENT ON TABLE otel_span_attrs_string IS 'String-typed span attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_attrs_string.span_id IS 'Foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_string.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_attrs_string.value IS 'String attribute value';

        COMMENT ON TABLE otel_span_attrs_int IS 'Integer-typed span attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_attrs_int.span_id IS 'Foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_int.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_attrs_int.value IS 'Integer attribute value (BIGINT for full range support)';

        COMMENT ON TABLE otel_span_attrs_double IS 'Double precision floating point span attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_attrs_double.span_id IS 'Foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_double.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_attrs_double.value IS 'Double precision floating point attribute value';

        COMMENT ON TABLE otel_span_attrs_bool IS 'Boolean-typed span attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_attrs_bool.span_id IS 'Foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_bool.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_attrs_bool.value IS 'Boolean attribute value';

        COMMENT ON TABLE otel_span_attrs_bytes IS 'Binary/bytes span attributes stored in dedicated table';
        COMMENT ON COLUMN otel_span_attrs_bytes.span_id IS 'Foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_bytes.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_attrs_bytes.value IS 'Binary attribute value stored as BYTEA';

        COMMENT ON TABLE otel_span_attrs_other IS 'JSONB catch-all for unpromoted, complex, or array-typed span attributes';
        COMMENT ON COLUMN otel_span_attrs_other.span_id IS 'Primary key and foreign key to otel_spans_fact';
        COMMENT ON COLUMN otel_span_attrs_other.attributes IS 'JSONB object containing all unpromoted attributes for this span';

        -- Span event attributes
        COMMENT ON TABLE otel_span_event_attrs_string IS 'String-typed span event attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_event_attrs_string.event_id IS 'Foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_string.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_event_attrs_string.value IS 'String attribute value';

        COMMENT ON TABLE otel_span_event_attrs_int IS 'Integer-typed span event attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_event_attrs_int.event_id IS 'Foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_int.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_event_attrs_int.value IS 'Integer attribute value (BIGINT for full range support)';

        COMMENT ON TABLE otel_span_event_attrs_double IS 'Double precision floating point span event attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_event_attrs_double.event_id IS 'Foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_double.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_event_attrs_double.value IS 'Double precision floating point attribute value';

        COMMENT ON TABLE otel_span_event_attrs_bool IS 'Boolean-typed span event attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_event_attrs_bool.event_id IS 'Foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_bool.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_event_attrs_bool.value IS 'Boolean attribute value';

        COMMENT ON TABLE otel_span_event_attrs_bytes IS 'Binary/bytes span event attributes stored in dedicated table';
        COMMENT ON COLUMN otel_span_event_attrs_bytes.event_id IS 'Foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_bytes.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_event_attrs_bytes.value IS 'Binary attribute value stored as BYTEA';

        COMMENT ON TABLE otel_span_event_attrs_other IS 'JSONB catch-all for unpromoted, complex, or array-typed span event attributes';
        COMMENT ON COLUMN otel_span_event_attrs_other.event_id IS 'Primary key and foreign key to otel_span_events';
        COMMENT ON COLUMN otel_span_event_attrs_other.attributes IS 'JSONB object containing all unpromoted attributes for this span event';

        -- Span link attributes
        COMMENT ON TABLE otel_span_link_attrs_string IS 'String-typed span link attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_link_attrs_string.link_id IS 'Foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_string.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_link_attrs_string.value IS 'String attribute value';

        COMMENT ON TABLE otel_span_link_attrs_int IS 'Integer-typed span link attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_link_attrs_int.link_id IS 'Foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_int.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_link_attrs_int.value IS 'Integer attribute value (BIGINT for full range support)';

        COMMENT ON TABLE otel_span_link_attrs_double IS 'Double precision floating point span link attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_link_attrs_double.link_id IS 'Foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_double.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_link_attrs_double.value IS 'Double precision floating point attribute value';

        COMMENT ON TABLE otel_span_link_attrs_bool IS 'Boolean-typed span link attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_span_link_attrs_bool.link_id IS 'Foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_bool.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_link_attrs_bool.value IS 'Boolean attribute value';

        COMMENT ON TABLE otel_span_link_attrs_bytes IS 'Binary/bytes span link attributes stored in dedicated table';
        COMMENT ON COLUMN otel_span_link_attrs_bytes.link_id IS 'Foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_bytes.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_span_link_attrs_bytes.value IS 'Binary attribute value stored as BYTEA';

        COMMENT ON TABLE otel_span_link_attrs_other IS 'JSONB catch-all for unpromoted, complex, or array-typed span link attributes';
        COMMENT ON COLUMN otel_span_link_attrs_other.link_id IS 'Primary key and foreign key to otel_span_links';
        COMMENT ON COLUMN otel_span_link_attrs_other.attributes IS 'JSONB object containing all unpromoted attributes for this span link';
    """)


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
