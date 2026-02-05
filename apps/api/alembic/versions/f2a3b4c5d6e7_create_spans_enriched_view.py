"""create spans enriched view

Revision ID: f2a3b4c5d6e7
Revises: f1a2b3c4d5e7
Create Date: 2024-12-19 10:15:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create v_otel_spans_enriched view.

    This view provides a denormalized, queryable representation of spans
    with all attributes aggregated from typed tables into a single JSONB column.

    Benefits:
    - Single query for all span + attribute data
    - No manual joins required by API layer
    - Efficient attribute filtering via JSONB operators
    - Includes resource and scope context
    - Parent-child span relationships
    """

    op.execute("""
        CREATE VIEW v_otel_spans_enriched AS
        WITH span_attributes AS (
            SELECT
                span_id,
                jsonb_object_agg(
                    ak.key,
                    CASE
                        WHEN ss.value IS NOT NULL THEN to_jsonb(ss.value)
                        WHEN si.value IS NOT NULL THEN to_jsonb(si.value)
                        WHEN sd.value IS NOT NULL THEN to_jsonb(sd.value)
                        WHEN sb.value IS NOT NULL THEN to_jsonb(sb.value)
                        WHEN sby.value IS NOT NULL THEN to_jsonb(sby.value)
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key IS NOT NULL) AS promoted_attributes
            FROM (
                SELECT DISTINCT span_id FROM otel_span_attrs_string
                UNION SELECT DISTINCT span_id FROM otel_span_attrs_int
                UNION SELECT DISTINCT span_id FROM otel_span_attrs_double
                UNION SELECT DISTINCT span_id FROM otel_span_attrs_bool
                UNION SELECT DISTINCT span_id FROM otel_span_attrs_bytes
            ) AS span_ids
            LEFT JOIN otel_span_attrs_string ss USING (span_id)
            LEFT JOIN otel_span_attrs_int si USING (span_id)
            LEFT JOIN otel_span_attrs_double sd USING (span_id)
            LEFT JOIN otel_span_attrs_bool sb USING (span_id)
            LEFT JOIN otel_span_attrs_bytes sby USING (span_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                ss.key_id, si.key_id, sd.key_id, sb.key_id, sby.key_id
            )
            GROUP BY span_id
        ),
        resource_attributes AS (
            SELECT
                resource_id,
                jsonb_object_agg(
                    ak.key,
                    CASE
                        WHEN rs.value IS NOT NULL THEN to_jsonb(rs.value)
                        WHEN ri.value IS NOT NULL THEN to_jsonb(ri.value)
                        WHEN rd.value IS NOT NULL THEN to_jsonb(rd.value)
                        WHEN rb.value IS NOT NULL THEN to_jsonb(rb.value)
                        WHEN rby.value IS NOT NULL THEN to_jsonb(rby.value)
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key IS NOT NULL) AS resource_attributes
            FROM (
                SELECT DISTINCT resource_id FROM otel_resource_attrs_string
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_int
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_double
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_bool
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_bytes
            ) AS resource_ids
            LEFT JOIN otel_resource_attrs_string rs USING (resource_id)
            LEFT JOIN otel_resource_attrs_int ri USING (resource_id)
            LEFT JOIN otel_resource_attrs_double rd USING (resource_id)
            LEFT JOIN otel_resource_attrs_bool rb USING (resource_id)
            LEFT JOIN otel_resource_attrs_bytes rby USING (resource_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                rs.key_id, ri.key_id, rd.key_id, rb.key_id, rby.key_id
            )
            GROUP BY resource_id
        ),
        scope_attributes AS (
            SELECT
                scope_id,
                jsonb_object_agg(
                    ak.key,
                    CASE
                        WHEN ss.value IS NOT NULL THEN to_jsonb(ss.value)
                        WHEN si.value IS NOT NULL THEN to_jsonb(si.value)
                        WHEN sd.value IS NOT NULL THEN to_jsonb(sd.value)
                        WHEN sb.value IS NOT NULL THEN to_jsonb(sb.value)
                        WHEN sby.value IS NOT NULL THEN to_jsonb(sby.value)
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key IS NOT NULL) AS scope_attributes
            FROM (
                SELECT DISTINCT scope_id FROM otel_scope_attrs_string
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_int
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_double
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_bool
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_bytes
            ) AS scope_ids
            LEFT JOIN otel_scope_attrs_string ss USING (scope_id)
            LEFT JOIN otel_scope_attrs_int si USING (scope_id)
            LEFT JOIN otel_scope_attrs_double sd USING (scope_id)
            LEFT JOIN otel_scope_attrs_bool sb USING (scope_id)
            LEFT JOIN otel_scope_attrs_bytes sby USING (scope_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                ss.key_id, si.key_id, sd.key_id, sb.key_id, sby.key_id
            )
            GROUP BY scope_id
        )
        SELECT
            s.span_id,
            s.trace_id,
            s.span_id_hex,
            s.parent_span_id_hex,
            s.name,
            s.kind_id,
            s.start_time_unix_nano,
            s.end_time_unix_nano,
            s.status_code_id,
            s.status_message,
            s.flags,

            -- Resource context
            s.resource_id,
            r.resource_hash,
            COALESCE(ra.resource_attributes, '{}'::jsonb) AS resource_attributes,

            -- Scope context
            s.scope_id,
            sc.scope_hash,
            sc.name AS scope_name,
            sc.version AS scope_version,
            COALESCE(sa.scope_attributes, '{}'::jsonb) AS scope_attributes,

            -- Span attributes (promoted + other)
            COALESCE(spa.promoted_attributes, '{}'::jsonb) ||
            COALESCE(s.attributes_other, '{}'::jsonb) AS attributes,

            -- Commonly queried fields for convenience
            (COALESCE(ra.resource_attributes, '{}'::jsonb) -> 'service.name')::text AS service_name,
            (COALESCE(ra.resource_attributes, '{}'::jsonb) -> 'service.namespace')::text AS service_namespace,
            (COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) -> 'http.method')::text AS http_method,
            (COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) -> 'http.status_code')::text AS http_status_code,
            (COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) -> 'error.type')::text AS error_type,

            -- Semantic type detection helpers
            CASE
                WHEN COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) ?| ARRAY['gen_ai.system', 'gen_ai.request.model', 'gen_ai.response.model'] THEN 'ai_agent'
                WHEN COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) ?| ARRAY['http.method', 'http.status_code', 'http.route'] THEN 'http'
                WHEN COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) ?| ARRAY['db.system', 'db.operation', 'db.statement'] THEN 'db'
                WHEN COALESCE(spa.promoted_attributes, '{}'::jsonb) || COALESCE(s.attributes_other, '{}'::jsonb) ?| ARRAY['messaging.system', 'messaging.operation'] THEN 'messaging'
                ELSE 'general'
            END AS semantic_type

        FROM otel_spans_fact s
        LEFT JOIN otel_resources_dim r ON s.resource_id = r.resource_id
        LEFT JOIN otel_scopes_dim sc ON s.scope_id = sc.scope_id
        LEFT JOIN span_attributes spa ON s.span_id = spa.span_id
        LEFT JOIN resource_attributes ra ON s.resource_id = ra.resource_id
        LEFT JOIN scope_attributes sa ON s.scope_id = sa.scope_id
    """)

    # Add helpful comments
    op.execute("""
        COMMENT ON VIEW v_otel_spans_enriched IS
        'Enriched span view with all attributes aggregated from typed tables.
         Provides ready-to-query denormalized representation including resource and scope context.
         Use JSONB operators on attributes column for efficient filtering:
         WHERE attributes @> ''{"http.status_code": 500}''
         WHERE attributes ? ''error.type''
         Includes parent_span_id_hex for trace tree reconstruction.';
    """)


def downgrade() -> None:
    """Drop v_otel_spans_enriched view."""
    op.execute("DROP VIEW IF EXISTS v_otel_spans_enriched")
