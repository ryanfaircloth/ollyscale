"""create log attribute tables

Revision ID: 151f87bcc9ff
Revises: 78d5e132a70b
Create Date: 2026-02-04 15:40:42.371939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '151f87bcc9ff'
down_revision: Union[str, Sequence[str], None] = '78d5e132a70b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create log attribute tables.

    Uses the hybrid storage pattern for log-specific attributes.
    """

    # log_attrs_string
    op.execute("""
        CREATE TABLE log_attrs_string (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_log_attrs_string_value ON log_attrs_string(key_id, value)")

    # log_attrs_int
    op.execute("""
        CREATE TABLE log_attrs_int (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)
    op.execute("CREATE INDEX idx_log_attrs_int_value ON log_attrs_int(key_id, value)")

    # log_attrs_double
    op.execute("""
        CREATE TABLE log_attrs_double (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # log_attrs_bool
    op.execute("""
        CREATE TABLE log_attrs_bool (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # log_attrs_bytes
    op.execute("""
        CREATE TABLE log_attrs_bytes (
            log_id BIGINT NOT NULL,
            key_id INT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )
    """)

    # log_attrs_other
    op.execute("""
        CREATE TABLE log_attrs_other (
            log_id BIGINT PRIMARY KEY,
            attributes JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_log_attrs_other_gin ON log_attrs_other USING GIN(attributes)")


def downgrade() -> None:
    """Drop log attribute tables."""
    op.execute("DROP TABLE IF EXISTS log_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS log_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS log_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS log_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS log_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS log_attrs_string CASCADE")
