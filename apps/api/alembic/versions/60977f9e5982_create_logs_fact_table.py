"""create logs fact table

Revision ID: 60977f9e5982
Revises: 45643391e8b3
Create Date: 2026-02-04 15:42:52.073881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60977f9e5982'
down_revision: Union[str, Sequence[str], None] = '45643391e8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create logs_fact table.

    Implements the log record data model with:
    - All OTLP log record fields
    - References to dimension tables
    - Optional trace correlation fields
    """

    op.execute("""
        CREATE TABLE logs_fact (
            log_id BIGSERIAL PRIMARY KEY,

            -- Resource and scope references
            resource_id BIGINT NOT NULL,
            scope_id BIGINT,

            -- Timing
            time_unix_nano BIGINT NOT NULL,
            observed_time_unix_nano BIGINT NOT NULL,

            -- Severity
            severity_number_id SMALLINT REFERENCES log_severity_numbers(severity_number_id),
            severity_text TEXT,

            -- Body
            body_type_id SMALLINT REFERENCES log_body_types(body_type_id),
            body JSONB,

            -- Trace correlation (optional fields)
            trace_id VARCHAR(32),
            span_id_hex VARCHAR(16),
            trace_flags INTEGER,

            -- Metadata
            dropped_attributes_count INTEGER DEFAULT 0,
            flags INTEGER DEFAULT 0
        )
    """)

    # Partition by time for efficient data lifecycle management
    # Note: Partitioning strategy will be added in a future migration


def downgrade() -> None:
    """Drop logs_fact table."""
    op.execute("DROP TABLE IF EXISTS logs_fact CASCADE")
