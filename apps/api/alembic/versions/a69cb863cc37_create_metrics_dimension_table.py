"""create metrics dimension table

Revision ID: a69cb863cc37
Revises: d2b90624419d
Create Date: 2026-02-04 15:39:07.104861

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a69cb863cc37"
down_revision: str | Sequence[str] | None = "d2b90624419d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create otel_metrics_dim dimension table.

    Implements metric metadata deduplication with two-hash strategy:
    - metric_hash: Full hash including description (unique per variant)
    - metric_identity_hash: Hash excluding description (groups variants)

    This allows multiple description variants for the same metric while
    supporting future alias management to consolidate semantically equivalent
    descriptions.
    """
    op.execute("""
        CREATE TABLE otel_metrics_dim (
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
    op.execute("CREATE INDEX idx_otel_metrics_dim_identity ON otel_metrics_dim(metric_identity_hash)")

    # Index for metric name lookups
    op.execute("CREATE INDEX idx_otel_metrics_dim_name ON otel_metrics_dim(name)")

    # Add table and column comments
    op.execute("""
        COMMENT ON TABLE otel_metrics_dim IS
        'Dimension table for OpenTelemetry metrics metadata with two-hash deduplication strategy supporting description variants';

        COMMENT ON COLUMN otel_metrics_dim.metric_id IS 'Primary key, auto-incrementing surrogate key for metric dimension';
        COMMENT ON COLUMN otel_metrics_dim.metric_hash IS 'SHA-256 hash including description, unique per variant';
        COMMENT ON COLUMN otel_metrics_dim.metric_identity_hash IS 'SHA-256 hash excluding description, groups variants of same metric';
        COMMENT ON COLUMN otel_metrics_dim.name IS 'OTLP metric name as defined by instrumentation';
        COMMENT ON COLUMN otel_metrics_dim.metric_type_id IS 'Foreign key to metric_types (Gauge, Sum, Histogram, etc.)';
        COMMENT ON COLUMN otel_metrics_dim.unit IS 'OTLP metric unit (e.g., ms, bytes, 1)';
        COMMENT ON COLUMN otel_metrics_dim.aggregation_temporality_id IS 'Foreign key to aggregation_temporalities (Delta, Cumulative)';
        COMMENT ON COLUMN otel_metrics_dim.is_monotonic IS 'For Sum metrics, whether values are monotonically increasing';
        COMMENT ON COLUMN otel_metrics_dim.description IS 'Metric description, can vary across variants';
        COMMENT ON COLUMN otel_metrics_dim.schema_url IS 'OTLP schema URL for semantic convention versioning';
        COMMENT ON COLUMN otel_metrics_dim.first_seen IS 'Timestamp when this metric configuration was first observed';
        COMMENT ON COLUMN otel_metrics_dim.last_seen IS 'Timestamp when this metric configuration was last observed, updated on ingestion';
    """)


def downgrade() -> None:
    """Drop otel_metrics_dim dimension table."""
    op.execute("DROP TABLE IF EXISTS otel_metrics_dim CASCADE")
