"""create metrics dimension table

Revision ID: a69cb863cc37
Revises: d2b90624419d
Create Date: 2026-02-04 15:39:07.104861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a69cb863cc37'
down_revision: Union[str, Sequence[str], None] = 'd2b90624419d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create metrics_dim dimension table.

    Implements metric metadata deduplication with two-hash strategy:
    - metric_hash: Full hash including description (unique per variant)
    - metric_identity_hash: Hash excluding description (groups variants)

    This allows multiple description variants for the same metric while
    supporting future alias management to consolidate semantically equivalent
    descriptions.
    """
    op.execute("""
        CREATE TABLE metrics_dim (
            metric_id BIGSERIAL PRIMARY KEY,

            -- Two-hash strategy for description variant support
            metric_hash VARCHAR(64) NOT NULL UNIQUE,
            metric_identity_hash VARCHAR(64) NOT NULL,

            -- Metric identification
            name TEXT NOT NULL,
            metric_type_id SMALLINT NOT NULL REFERENCES metric_types(metric_type_id),
            unit TEXT,
            aggregation_temporality_id SMALLINT REFERENCES aggregation_temporalities(temporality_id),
            is_monotonic BOOLEAN,

            -- Description can vary for same metric identity
            description TEXT,

            -- Schema versioning
            schema_url TEXT,

            -- Temporal tracking
            first_seen TIMESTAMPTZ DEFAULT NOW(),
            last_seen TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Index for grouping description variants
    op.execute(
        "CREATE INDEX idx_metrics_dim_identity ON metrics_dim(metric_identity_hash)"
    )

    # Index for metric name lookups
    op.execute("CREATE INDEX idx_metrics_dim_name ON metrics_dim(name)")


def downgrade() -> None:
    """Drop metrics_dim dimension table."""
    op.execute("DROP TABLE IF EXISTS metrics_dim CASCADE")
