"""create log attribute tables

Revision ID: 151f87bcc9ff
Revises: 78d5e132a70b
Create Date: 2026-02-04 15:40:42.371939

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "151f87bcc9ff"
down_revision: str | Sequence[str] | None = "78d5e132a70b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create log attribute tables.

    Uses the hybrid storage pattern for log-specific attributes.
    """

    # otel_log_attrs_string
    op.execute("""
        CREATE TABLE otel_log_attrs_string (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_log_attrs_string_value ON otel_log_attrs_string(key_id, value)")

    # otel_log_attrs_int
    op.execute("""
        CREATE TABLE otel_log_attrs_int (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_otel_log_attrs_int_value ON otel_log_attrs_int(key_id, value)")

    # otel_log_attrs_double
    op.execute("""
        CREATE TABLE otel_log_attrs_double (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # otel_log_attrs_bool
    op.execute("""
        CREATE TABLE otel_log_attrs_bool (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # otel_log_attrs_bytes
    op.execute("""
        CREATE TABLE otel_log_attrs_bytes (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # otel_log_attrs_other
    op.execute("""
        CREATE TABLE otel_log_attrs_other (
            log_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_otel_log_attrs_other_gin ON otel_log_attrs_other USING GIN(attributes)")

    # Add table and column comments
    op.execute("""
        COMMENT ON TABLE otel_log_attrs_string IS 'String-typed log attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_log_attrs_string.log_id IS 'Foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_string.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_log_attrs_string.value IS 'String attribute value';

        COMMENT ON TABLE otel_log_attrs_int IS 'Integer-typed log attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_log_attrs_int.log_id IS 'Foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_int.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_log_attrs_int.value IS 'Integer attribute value (BIGINT for full range support)';

        COMMENT ON TABLE otel_log_attrs_double IS 'Double precision floating point log attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_log_attrs_double.log_id IS 'Foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_double.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_log_attrs_double.value IS 'Double precision floating point attribute value';

        COMMENT ON TABLE otel_log_attrs_bool IS 'Boolean-typed log attributes stored in dedicated table for query performance';
        COMMENT ON COLUMN otel_log_attrs_bool.log_id IS 'Foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_bool.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_log_attrs_bool.value IS 'Boolean attribute value';

        COMMENT ON TABLE otel_log_attrs_bytes IS 'Binary/bytes log attributes stored in dedicated table';
        COMMENT ON COLUMN otel_log_attrs_bytes.log_id IS 'Foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_bytes.key_id IS 'Foreign key to attribute_keys for attribute name';
        COMMENT ON COLUMN otel_log_attrs_bytes.value IS 'Binary attribute value stored as BYTEA';

        COMMENT ON TABLE otel_log_attrs_other IS 'JSONB catch-all for unpromoted, complex, or array-typed log attributes';
        COMMENT ON COLUMN otel_log_attrs_other.log_id IS 'Primary key and foreign key to otel_logs_fact';
        COMMENT ON COLUMN otel_log_attrs_other.attributes IS 'JSONB object containing all unpromoted attributes for this log record';
    """)


def downgrade() -> None:
    """Drop log attribute tables."""
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_string CASCADE")
