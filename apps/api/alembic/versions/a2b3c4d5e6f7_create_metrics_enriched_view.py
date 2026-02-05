"""create metrics enriched view

Revision ID: a2b3c4d5e6f7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-04 18:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create v_otel_metrics_enriched view with all metric types unified.

    Phase 4 simplified view: No resource/scope attribute aggregation (for now).
    Includes basic dimensions only.
    """

    op.execute("""
        CREATE OR REPLACE VIEW v_otel_metrics_enriched AS
        -- Number data points (Gauge=1, Sum=2)
        SELECT
            dp.data_point_id,
            dp.metric_id,
            m.name AS metric_name,
            m.metric_type_id,
            mt.name AS metric_type,
            m.unit,
            m.is_monotonic,
            m.aggregation_temporality_id,
            at.name AS aggregation_temporality,
            m.description AS metric_description,
            m.schema_url AS metric_schema_url,
            dp.resource_id,
            r.service_name,
            r.service_namespace,
            dp.scope_id,
            s.name AS scope_name,
            s.version AS scope_version,
            to_timestamp(dp.start_time_unix_nano / 1e9) AS start_time,
            to_timestamp(dp.time_unix_nano / 1e9) AS "time",
            dp.start_time_unix_nano,
            dp.time_unix_nano,
            dp.value_int,
            dp.value_double,
            CAST(COALESCE(dp.value_double, dp.value_int::double precision) AS double precision) AS value,
            NULL::bigint AS count,
            NULL::double precision AS sum,
            NULL::double precision AS min,
            NULL::double precision AS max,
            NULL::double precision[] AS explicit_bounds,
            NULL::bigint[] AS bucket_counts,
            NULL::integer AS scale,
            NULL::bigint AS zero_count,
            NULL::integer AS positive_offset,
            NULL::bigint[] AS positive_bucket_counts,
            NULL::integer AS negative_offset,
            NULL::bigint[] AS negative_bucket_counts,
            NULL::jsonb AS quantile_values,
            dp.flags,
            dp.exemplars,
            dp.attributes_other
        FROM otel_metrics_data_points_number dp
        INNER JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
        INNER JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
        INNER JOIN otel_resources_dim r ON dp.resource_id = r.resource_id
        INNER JOIN otel_scopes_dim s ON dp.scope_id = s.scope_id
        LEFT JOIN aggregation_temporalities at ON m.aggregation_temporality_id = at.temporality_id

        UNION ALL

        -- Histogram data points (type=3)
        SELECT
            dp.data_point_id,
            dp.metric_id,
            m.name AS metric_name,
            m.metric_type_id,
            mt.name AS metric_type,
            m.unit,
            m.is_monotonic,
            m.aggregation_temporality_id,
            at.name AS aggregation_temporality,
            m.description AS metric_description,
            m.schema_url AS metric_schema_url,
            dp.resource_id,
            r.service_name,
            r.service_namespace,
            dp.scope_id,
            s.name AS scope_name,
            s.version AS scope_version,
            to_timestamp(dp.start_time_unix_nano / 1e9) AS start_time,
            to_timestamp(dp.time_unix_nano / 1e9) AS "time",
            dp.start_time_unix_nano,
            dp.time_unix_nano,
            NULL::bigint AS value_int,
            NULL::double precision AS value_double,
            dp.sum AS value,
            dp.count,
            dp.sum,
            dp.min,
            dp.max,
            dp.explicit_bounds,
            dp.bucket_counts,
            NULL::integer AS scale,
            NULL::bigint AS zero_count,
            NULL::integer AS positive_offset,
            NULL::bigint[] AS positive_bucket_counts,
            NULL::integer AS negative_offset,
            NULL::bigint[] AS negative_bucket_counts,
            NULL::jsonb AS quantile_values,
            dp.flags,
            dp.exemplars,
            dp.attributes_other
        FROM otel_metrics_data_points_histogram dp
        INNER JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
        INNER JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
        INNER JOIN otel_resources_dim r ON dp.resource_id = r.resource_id
        INNER JOIN otel_scopes_dim s ON dp.scope_id = s.scope_id
        LEFT JOIN aggregation_temporalities at ON m.aggregation_temporality_id = at.temporality_id

        UNION ALL

        -- Exponential Histogram data points (type=4)
        SELECT
            dp.data_point_id,
            dp.metric_id,
            m.name AS metric_name,
            m.metric_type_id,
            mt.name AS metric_type,
            m.unit,
            m.is_monotonic,
            m.aggregation_temporality_id,
            at.name AS aggregation_temporality,
            m.description AS metric_description,
            m.schema_url AS metric_schema_url,
            dp.resource_id,
            r.service_name,
            r.service_namespace,
            dp.scope_id,
            s.name AS scope_name,
            s.version AS scope_version,
            to_timestamp(dp.start_time_unix_nano / 1e9) AS start_time,
            to_timestamp(dp.time_unix_nano / 1e9) AS "time",
            dp.start_time_unix_nano,
            dp.time_unix_nano,
            NULL::bigint AS value_int,
            NULL::double precision AS value_double,
            dp.sum AS value,
            dp.count,
            dp.sum,
            NULL::double precision AS min,
            NULL::double precision AS max,
            NULL::double precision[] AS explicit_bounds,
            NULL::bigint[] AS bucket_counts,
            dp.scale,
            dp.zero_count,
            dp.positive_offset,
            dp.positive_bucket_counts,
            dp.negative_offset,
            dp.negative_bucket_counts,
            NULL::jsonb AS quantile_values,
            dp.flags,
            dp.exemplars,
            dp.attributes_other
        FROM otel_metrics_data_points_exp_histogram dp
        INNER JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
        INNER JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
        INNER JOIN otel_resources_dim r ON dp.resource_id = r.resource_id
        INNER JOIN otel_scopes_dim s ON dp.scope_id = s.scope_id
        LEFT JOIN aggregation_temporalities at ON m.aggregation_temporality_id = at.temporality_id

        UNION ALL

        -- Summary data points (type=5)
        SELECT
            dp.data_point_id,
            dp.metric_id,
            m.name AS metric_name,
            m.metric_type_id,
            mt.name AS metric_type,
            m.unit,
            m.is_monotonic,
            m.aggregation_temporality_id,
            at.name AS aggregation_temporality,
            m.description AS metric_description,
            m.schema_url AS metric_schema_url,
            dp.resource_id,
            r.service_name,
            r.service_namespace,
            dp.scope_id,
            s.name AS scope_name,
            s.version AS scope_version,
            to_timestamp(dp.start_time_unix_nano / 1e9) AS start_time,
            to_timestamp(dp.time_unix_nano / 1e9) AS "time",
            dp.start_time_unix_nano,
            dp.time_unix_nano,
            NULL::bigint AS value_int,
            NULL::double precision AS value_double,
            dp.sum AS value,
            dp.count,
            dp.sum,
            NULL::double precision AS min,
            NULL::double precision AS max,
            NULL::double precision[] AS explicit_bounds,
            NULL::bigint[] AS bucket_counts,
            NULL::integer AS scale,
            NULL::bigint AS zero_count,
            NULL::integer AS positive_offset,
           NULL::bigint[] AS positive_bucket_counts,
            NULL::integer AS negative_offset,
            NULL::bigint[] AS negative_bucket_counts,
            dp.quantile_values,
            dp.flags,
            NULL::jsonb AS exemplars,
            dp.attributes_other
        FROM otel_metrics_data_points_summary dp
        INNER JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
        INNER JOIN metric_types mt ON m.metric_type_id = mt.metric_type_id
        INNER JOIN otel_resources_dim r ON dp.resource_id = r.resource_id
        INNER JOIN otel_scopes_dim s ON dp.scope_id = s.scope_id
        LEFT JOIN aggregation_temporalities at ON m.aggregation_temporality_id = at.temporality_id
    """)

    op.execute("""
        COMMENT ON VIEW v_otel_metrics_enriched IS
        'Unified view of all OTLP metrics with enriched metadata (Phase 4 simplified).
         Combines number (Gauge/Sum), histogram, exponential histogram, and summary
         data points with metric dimensions, resource identification, and scope info.
         Use metric_type_id to filter: 1=Gauge, 2=Sum, 3=Histogram, 4=ExponentialHistogram, 5=Summary.
         Type-specific columns are NULL for non-applicable types.'
    """)


def downgrade() -> None:
    """Drop the metrics enriched view."""
    op.execute("DROP VIEW IF EXISTS v_otel_metrics_enriched")
