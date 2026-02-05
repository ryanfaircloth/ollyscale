"""create logs enriched view

Revision ID: e1f2a3b4c5d6
Revises: 168b8d294a0c
Create Date: 2026-02-04 16:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create v_otel_logs_enriched view.

    This view provides a denormalized, queryable representation of logs
    with all attributes aggregated from typed tables into a single JSONB column.

    Benefits:
    - Single query for all log + attribute data
    - No manual joins required by API layer
    - Efficient attribute filtering via JSONB operators
    - Includes resource and scope context
    """

    op.execute("""
        CREATE VIEW v_otel_logs_enriched AS
        WITH log_attributes AS (
            SELECT
                log_id,
                jsonb_object_agg(
                    ak.key_name,
                    CASE
                        WHEN ls.value IS NOT NULL THEN to_jsonb(ls.value)
                        WHEN li.value IS NOT NULL THEN to_jsonb(li.value)
                        WHEN ld.value IS NOT NULL THEN to_jsonb(ld.value)
                        WHEN lb.value IS NOT NULL THEN to_jsonb(lb.value)
                        WHEN lby.value IS NOT NULL THEN to_jsonb(lby.value)
                        WHEN lo.value IS NOT NULL THEN lo.value
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key_name IS NOT NULL) AS promoted_attributes
            FROM (
                SELECT DISTINCT log_id FROM otel_log_attrs_string
                UNION SELECT DISTINCT log_id FROM otel_log_attrs_int
                UNION SELECT DISTINCT log_id FROM otel_log_attrs_double
                UNION SELECT DISTINCT log_id FROM otel_log_attrs_bool
                UNION SELECT DISTINCT log_id FROM otel_log_attrs_bytes
                UNION SELECT DISTINCT log_id FROM otel_log_attrs_other
            ) AS log_ids
            LEFT JOIN otel_log_attrs_string ls USING (log_id)
            LEFT JOIN otel_log_attrs_int li USING (log_id)
            LEFT JOIN otel_log_attrs_double ld USING (log_id)
            LEFT JOIN otel_log_attrs_bool lb USING (log_id)
            LEFT JOIN otel_log_attrs_bytes lby USING (log_id)
            LEFT JOIN otel_log_attrs_other lo USING (log_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                ls.key_id, li.key_id, ld.key_id, lb.key_id, lby.key_id, lo.key_id
            )
            GROUP BY log_id
        ),
        resource_attributes AS (
            SELECT
                resource_id,
                jsonb_object_agg(
                    ak.key_name,
                    CASE
                        WHEN rs.value IS NOT NULL THEN to_jsonb(rs.value)
                        WHEN ri.value IS NOT NULL THEN to_jsonb(ri.value)
                        WHEN rd.value IS NOT NULL THEN to_jsonb(rd.value)
                        WHEN rb.value IS NOT NULL THEN to_jsonb(rb.value)
                        WHEN rby.value IS NOT NULL THEN to_jsonb(rby.value)
                        WHEN ro.value IS NOT NULL THEN ro.value
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key_name IS NOT NULL) AS resource_attributes
            FROM (
                SELECT DISTINCT resource_id FROM otel_resource_attrs_string
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_int
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_double
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_bool
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_bytes
                UNION SELECT DISTINCT resource_id FROM otel_resource_attrs_other
            ) AS resource_ids
            LEFT JOIN otel_resource_attrs_string rs USING (resource_id)
            LEFT JOIN otel_resource_attrs_int ri USING (resource_id)
            LEFT JOIN otel_resource_attrs_double rd USING (resource_id)
            LEFT JOIN otel_resource_attrs_bool rb USING (resource_id)
            LEFT JOIN otel_resource_attrs_bytes rby USING (resource_id)
            LEFT JOIN otel_resource_attrs_other ro USING (resource_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                rs.key_id, ri.key_id, rd.key_id, rb.key_id, rby.key_id, ro.key_id
            )
            GROUP BY resource_id
        ),
        scope_attributes AS (
            SELECT
                scope_id,
                jsonb_object_agg(
                    ak.key_name,
                    CASE
                        WHEN ss.value IS NOT NULL THEN to_jsonb(ss.value)
                        WHEN si.value IS NOT NULL THEN to_jsonb(si.value)
                        WHEN sd.value IS NOT NULL THEN to_jsonb(sd.value)
                        WHEN sb.value IS NOT NULL THEN to_jsonb(sb.value)
                        WHEN sby.value IS NOT NULL THEN to_jsonb(sby.value)
                        WHEN so.value IS NOT NULL THEN so.value
                        ELSE 'null'::jsonb
                    END
                ) FILTER (WHERE ak.key_name IS NOT NULL) AS scope_attributes
            FROM (
                SELECT DISTINCT scope_id FROM otel_scope_attrs_string
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_int
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_double
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_bool
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_bytes
                UNION SELECT DISTINCT scope_id FROM otel_scope_attrs_other
            ) AS scope_ids
            LEFT JOIN otel_scope_attrs_string ss USING (scope_id)
            LEFT JOIN otel_scope_attrs_int si USING (scope_id)
            LEFT JOIN otel_scope_attrs_double sd USING (scope_id)
            LEFT JOIN otel_scope_attrs_bool sb USING (scope_id)
            LEFT JOIN otel_scope_attrs_bytes sby USING (scope_id)
            LEFT JOIN otel_scope_attrs_other so USING (scope_id)
            LEFT JOIN attribute_keys ak ON ak.key_id = COALESCE(
                ss.key_id, si.key_id, sd.key_id, sb.key_id, sby.key_id, so.key_id
            )
            GROUP BY scope_id
        )
        SELECT
            l.log_id,
            l.time_unix_nano,
            l.observed_time_unix_nano,
            l.severity_number,
            l.severity_text,
            l.body_type_id,
            l.body,
            l.trace_id,
            l.span_id_hex,
            l.trace_flags,
            l.dropped_attributes_count,
            l.flags,

            -- Resource context
            l.resource_id,
            r.resource_hash,
            COALESCE(ra.resource_attributes, '{}'::jsonb) AS resource_attributes,

            -- Scope context
            l.scope_id,
            s.scope_hash,
            s.name AS scope_name,
            s.version AS scope_version,
            COALESCE(sa.scope_attributes, '{}'::jsonb) AS scope_attributes,

            -- Log attributes (promoted + other)
            COALESCE(la.promoted_attributes, '{}'::jsonb) ||
            COALESCE(l.attributes_other, '{}'::jsonb) AS attributes,

            -- Commonly queried fields for convenience
            (COALESCE(ra.resource_attributes, '{}'::jsonb) -> 'service.name')::text AS service_name,
            (COALESCE(ra.resource_attributes, '{}'::jsonb) -> 'service.namespace')::text AS service_namespace,
            (COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) -> 'log.level')::text AS log_level,
            (COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) -> 'error.type')::text AS error_type,

            -- Semantic type detection helpers
            CASE
                WHEN COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) ?| ARRAY['gen_ai.system', 'gen_ai.request.model', 'gen_ai.response.model'] THEN 'ai_agent'
                WHEN COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) ?| ARRAY['http.method', 'http.status_code', 'http.route'] THEN 'http'
                WHEN COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) ?| ARRAY['db.system', 'db.operation', 'db.statement'] THEN 'db'
                WHEN COALESCE(la.promoted_attributes, '{}'::jsonb) || COALESCE(l.attributes_other, '{}'::jsonb) ?| ARRAY['messaging.system', 'messaging.operation'] THEN 'messaging'
                ELSE 'general'
            END AS semantic_type

        FROM otel_logs_fact l
        LEFT JOIN otel_resources_dim r ON l.resource_id = r.resource_id
        LEFT JOIN otel_scopes_dim s ON l.scope_id = s.scope_id
        LEFT JOIN log_attributes la ON l.log_id = la.log_id
        LEFT JOIN resource_attributes ra ON l.resource_id = ra.resource_id
        LEFT JOIN scope_attributes sa ON l.scope_id = sa.scope_id
    """)

    # Add helpful comments
    op.execute("""
        COMMENT ON VIEW v_otel_logs_enriched IS
        'Enriched log view with all attributes aggregated from typed tables.
         Provides ready-to-query denormalized representation including resource and scope context.
         Use JSONB operators on attributes column for efficient filtering:
         WHERE attributes @> ''{"http.status_code": 500}''
         WHERE attributes ? ''error.type''';
    """)


def downgrade() -> None:
    """Drop v_otel_logs_enriched view."""
    op.execute("DROP VIEW IF EXISTS v_otel_logs_enriched")
