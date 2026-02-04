"""add trace correlation foreign keys not valid

Revision ID: c846417c2785
Revises: 168b8d294a0c
Create Date: 2026-02-04 15:44:07.428963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c846417c2785'
down_revision: Union[str, Sequence[str], None] = '168b8d294a0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trace correlation foreign keys with NOT VALID constraint.

    These foreign keys provide query optimizer hints without enforcing
    referential integrity, which is appropriate for:
    1. Out-of-order OTLP data arrival
    2. Partial trace collection
    3. Cross-service trace sampling
    
    Foreign keys added:
    - logs_fact → spans_fact (trace correlation)
    - spans_fact → spans_fact (parent-child relationships)
    - span_links → spans_fact (linked span backreference)
    """

    # First, add unique constraint on spans_fact for FK target
    # This is needed for the foreign key references
    op.execute("""
        ALTER TABLE spans_fact 
        ADD CONSTRAINT uq_spans_trace_span_id 
        UNIQUE (trace_id, span_id_hex)
    """)

    # FK from logs to spans for trace correlation
    # NOT VALID means: provide optimizer hints, don't enforce
    op.execute("""
        ALTER TABLE logs_fact 
        ADD CONSTRAINT fk_logs_span_correlation 
        FOREIGN KEY (trace_id, span_id_hex) 
        REFERENCES spans_fact(trace_id, span_id_hex) 
        NOT VALID
    """)

    # FK from spans to parent span (self-referencing)
    # Uses same trace_id with parent_span_id_hex
    op.execute("""
        ALTER TABLE spans_fact 
        ADD CONSTRAINT fk_spans_parent 
        FOREIGN KEY (trace_id, parent_span_id_hex) 
        REFERENCES spans_fact(trace_id, span_id_hex) 
        NOT VALID
    """)

    # FK from span_links to linked span (backreference)
    # Allows traversing span links in reverse
    op.execute("""
        ALTER TABLE span_links 
        ADD CONSTRAINT fk_span_links_target 
        FOREIGN KEY (linked_trace_id, linked_span_id_hex) 
        REFERENCES spans_fact(trace_id, span_id_hex) 
        NOT VALID
    """)


def downgrade() -> None:
    """Drop trace correlation foreign keys."""
    op.execute("ALTER TABLE span_links DROP CONSTRAINT IF EXISTS fk_span_links_target")
    op.execute("ALTER TABLE spans_fact DROP CONSTRAINT IF EXISTS fk_spans_parent")
    op.execute("ALTER TABLE logs_fact DROP CONSTRAINT IF EXISTS fk_logs_span_correlation")
    op.execute("ALTER TABLE spans_fact DROP CONSTRAINT IF EXISTS uq_spans_trace_span_id")
