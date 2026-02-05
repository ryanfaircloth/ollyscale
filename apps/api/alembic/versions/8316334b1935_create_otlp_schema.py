"""create_otlp_schema

Comprehensive OTLP schema for fresh deployment with timestamp+nanos pattern.

Revision ID: 8316334b1935
Revises:
Create Date: 2026-02-05 11:19:58.922980

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8316334b1935"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create complete OTLP schema with denormalized attributes."""

    # 1. Attribute Keys Registry
    op.execute("""
        CREATE TABLE attribute_keys (
            key_id BIGSERIAL PRIMARY KEY,
            key VARCHAR(255) NOT NULL UNIQUE
        )""")
    op.execute("CREATE UNIQUE INDEX idx_attribute_keys_key ON attribute_keys(key)")
    op.execute("COMMENT ON TABLE attribute_keys IS 'Deduplication registry for attribute keys across all signals'")

    # 1b. Reference/Lookup Tables
    op.execute("""
        CREATE TABLE log_severity_numbers (
            severity_number SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute(
        "COMMENT ON TABLE log_severity_numbers IS 'OTLP log severity levels (0-24) per OpenTelemetry specification'"
    )
    op.execute("""
        INSERT INTO log_severity_numbers (severity_number, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified severity'),
            (1, 'TRACE', 'Trace-level message (most verbose)'),
            (5, 'DEBUG', 'Debug-level message'),
            (9, 'INFO', 'Informational message'),
            (13, 'WARN', 'Warning message'),
            (17, 'ERROR', 'Error message'),
            (21, 'FATAL', 'Fatal error message (most severe)')""")

    op.execute("""
        CREATE TABLE log_body_types (
            body_type_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute("COMMENT ON TABLE log_body_types IS 'OTLP AnyValue types for log body field'")
    op.execute("""
        INSERT INTO log_body_types (body_type_id, name, description) VALUES
            (0, 'EMPTY', 'Empty/null body'),
            (1, 'STRING', 'String body'),
            (2, 'INT', 'Integer body'),
            (3, 'DOUBLE', 'Double precision body'),
            (4, 'BOOL', 'Boolean body'),
            (5, 'BYTES', 'Bytes body'),
            (6, 'ARRAY', 'Array body'),
            (7, 'KVLIST', 'Key-value list body')""")

    op.execute("""
        CREATE TABLE span_kinds (
            kind_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute("COMMENT ON TABLE span_kinds IS 'OTLP span kinds per OpenTelemetry specification'")
    op.execute("""
        INSERT INTO span_kinds (kind_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified span kind'),
            (1, 'INTERNAL', 'Internal operation within application'),
            (2, 'SERVER', 'Server-side handling of RPC or HTTP request'),
            (3, 'CLIENT', 'Client-side RPC or HTTP request'),
            (4, 'PRODUCER', 'Message producer (async operations)'),
            (5, 'CONSUMER', 'Message consumer (async operations)')""")

    op.execute("""
        CREATE TABLE status_codes (
            status_code_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute("COMMENT ON TABLE status_codes IS 'OTLP status codes per OpenTelemetry specification'")
    op.execute("""
        INSERT INTO status_codes (status_code_id, name, description) VALUES
            (0, 'UNSET', 'Default status - operation not explicitly set'),
            (1, 'OK', 'Operation completed successfully'),
            (2, 'ERROR', 'Operation failed with error')""")

    op.execute("""
        CREATE TABLE metric_types (
            metric_type_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute("COMMENT ON TABLE metric_types IS 'OTLP metric data types'")
    op.execute("""
        INSERT INTO metric_types (metric_type_id, name, description) VALUES
            (1, 'GAUGE', 'Point-in-time measurement (no aggregation)'),
            (2, 'SUM', 'Cumulative or delta sum aggregation'),
            (3, 'HISTOGRAM', 'Distribution with explicit bucket boundaries'),
            (4, 'EXP_HISTOGRAM', 'Distribution with exponential bucket boundaries'),
            (5, 'SUMMARY', 'Summary statistics with quantiles')""")

    op.execute("""
        CREATE TABLE aggregation_temporalities (
            temporality_id SMALLINT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT
        )""")
    op.execute("COMMENT ON TABLE aggregation_temporalities IS 'OTLP metric aggregation temporality'")
    op.execute("""
        INSERT INTO aggregation_temporalities (temporality_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified temporality'),
            (1, 'DELTA', 'Change since last measurement interval'),
            (2, 'CUMULATIVE', 'Total accumulated since start')""")

    # 2. Resources Dimension
    op.execute("""
        CREATE TABLE otel_resources_dim (
            resource_id BIGSERIAL PRIMARY KEY,
            resource_hash VARCHAR(64) NOT NULL UNIQUE,
            service_name VARCHAR(255),
            service_namespace VARCHAR(255),
            schema_url TEXT,
            first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            dropped_attributes_count INTEGER NOT NULL DEFAULT 0
        )""")
    op.execute("CREATE UNIQUE INDEX idx_otel_resources_hash ON otel_resources_dim(resource_hash)")
    op.execute("CREATE INDEX idx_otel_resources_service ON otel_resources_dim(service_name, service_namespace)")
    op.execute("CREATE INDEX idx_otel_resources_last_seen ON otel_resources_dim(last_seen)")
    op.execute("COMMENT ON TABLE otel_resources_dim IS 'Resource dimension with hash-based deduplication'")

    # 3. Scopes Dimension
    op.execute("""
        CREATE TABLE otel_scopes_dim (
            scope_id BIGSERIAL PRIMARY KEY,
            scope_hash VARCHAR(64) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(255),
            schema_url TEXT,
            first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            dropped_attributes_count INTEGER NOT NULL DEFAULT 0
        )""")
    op.execute("CREATE UNIQUE INDEX idx_otel_scopes_hash ON otel_scopes_dim(scope_hash)")
    op.execute("CREATE INDEX idx_otel_scopes_name ON otel_scopes_dim(name)")
    op.execute("CREATE INDEX idx_otel_scopes_last_seen ON otel_scopes_dim(last_seen)")
    op.execute("COMMENT ON TABLE otel_scopes_dim IS 'Instrumentation scope/library dimension'")

    # 3b. Resource Attribute Tables
    op.execute("""
        CREATE TABLE otel_resource_attrs_string (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_string_key_value ON otel_resource_attrs_string(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_string IS 'Promoted string resource attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_resource_attrs_int (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_int_key_value ON otel_resource_attrs_int(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_int IS 'Promoted integer resource attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_resource_attrs_double (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_double_key_value ON otel_resource_attrs_double(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_double IS 'Promoted double resource attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_resource_attrs_bool (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_bool_key ON otel_resource_attrs_bool(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_bool IS 'Promoted boolean resource attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_resource_attrs_bytes (
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (resource_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_bytes_key ON otel_resource_attrs_bytes(key_id)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_bytes IS 'Promoted bytes resource attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_resource_attrs_other (
            resource_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_resources_dim(resource_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        )""")
    op.execute("CREATE INDEX idx_otel_resource_attrs_other_gin ON otel_resource_attrs_other USING gin(attributes)")
    op.execute(
        "COMMENT ON TABLE otel_resource_attrs_other IS 'JSONB catch-all for unpromoted resource attributes (complex types, unknown keys)'"
    )

    # 3c. Scope Attribute Tables
    op.execute("""
        CREATE TABLE otel_scope_attrs_string (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_string_key_value ON otel_scope_attrs_string(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_string IS 'Promoted string scope attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_scope_attrs_int (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_int_key_value ON otel_scope_attrs_int(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_int IS 'Promoted integer scope attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_scope_attrs_double (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_double_key_value ON otel_scope_attrs_double(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_double IS 'Promoted double scope attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_scope_attrs_bool (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_bool_key ON otel_scope_attrs_bool(key_id, value)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_bool IS 'Promoted boolean scope attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_scope_attrs_bytes (
            scope_id BIGINT NOT NULL REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (scope_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_bytes_key ON otel_scope_attrs_bytes(key_id)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_bytes IS 'Promoted bytes scope attributes per attribute-promotion.yaml config'"
    )

    op.execute("""
        CREATE TABLE otel_scope_attrs_other (
            scope_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_scopes_dim(scope_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        )""")
    op.execute("CREATE INDEX idx_otel_scope_attrs_other_gin ON otel_scope_attrs_other USING gin(attributes)")
    op.execute(
        "COMMENT ON TABLE otel_scope_attrs_other IS 'JSONB catch-all for unpromoted scope attributes (complex types, unknown keys)'"
    )

    # 4. Logs Fact Table
    op.execute("""
        CREATE TABLE otel_logs_fact (
            log_id BIGSERIAL PRIMARY KEY,
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
            scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),

            -- Timing with full nanosecond precision
            time TIMESTAMP WITH TIME ZONE NOT NULL,
            time_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            observed_time TIMESTAMP WITH TIME ZONE NOT NULL,
            observed_time_nanos_fraction SMALLINT NOT NULL DEFAULT 0,

            -- Severity
            severity_number SMALLINT,
            severity_text TEXT,

            -- Body
            body_type_id SMALLINT,
            body JSONB,

            -- Trace correlation
            trace_id VARCHAR(32),
            span_id_hex VARCHAR(16),
            trace_flags INTEGER,

            -- Attributes catch-all
            attributes_other JSONB,

            -- Metadata
            dropped_attributes_count INTEGER NOT NULL DEFAULT 0,
            flags INTEGER NOT NULL DEFAULT 0
        )""")
    op.execute("CREATE INDEX idx_otel_logs_time ON otel_logs_fact(time, time_nanos_fraction)")
    op.execute("CREATE INDEX idx_otel_logs_resource ON otel_logs_fact(resource_id)")
    op.execute(
        "CREATE INDEX idx_otel_logs_severity ON otel_logs_fact(severity_number) WHERE severity_number IS NOT NULL"
    )
    op.execute("CREATE INDEX idx_otel_logs_trace ON otel_logs_fact(trace_id, span_id_hex) WHERE trace_id IS NOT NULL")
    op.execute(
        "CREATE INDEX idx_otel_logs_attrs_other_gin ON otel_logs_fact USING gin(attributes_other) WHERE attributes_other IS NOT NULL"
    )
    op.execute("COMMENT ON TABLE otel_logs_fact IS 'Log records fact table with timestamp+nanos precision'")

    # 5. Log Attribute Tables
    op.execute("""
        CREATE TABLE otel_log_attrs_string (
            log_id BIGINT NOT NULL REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_string_log ON otel_log_attrs_string(log_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_string_key ON otel_log_attrs_string(key_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_string_value ON otel_log_attrs_string(value)")

    op.execute("""
        CREATE TABLE otel_log_attrs_int (
            log_id BIGINT NOT NULL REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_int_log ON otel_log_attrs_int(log_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_int_key ON otel_log_attrs_int(key_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_int_value ON otel_log_attrs_int(value)")

    op.execute("""
        CREATE TABLE otel_log_attrs_double (
            log_id BIGINT NOT NULL REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_double_log ON otel_log_attrs_double(log_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_double_key ON otel_log_attrs_double(key_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_double_value ON otel_log_attrs_double(value)")

    op.execute("""
        CREATE TABLE otel_log_attrs_bool (
            log_id BIGINT NOT NULL REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_bool_log ON otel_log_attrs_bool(log_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_bool_key ON otel_log_attrs_bool(key_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_bool_value ON otel_log_attrs_bool(value)")

    op.execute("""
        CREATE TABLE otel_log_attrs_bytes (
            log_id BIGINT NOT NULL REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (log_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_bytes_log ON otel_log_attrs_bytes(log_id)")
    op.execute("CREATE INDEX idx_otel_log_attrs_bytes_key ON otel_log_attrs_bytes(key_id)")

    op.execute("""
        CREATE TABLE otel_log_attrs_other (
            log_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_logs_fact(log_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        )""")
    op.execute("CREATE INDEX idx_otel_log_attrs_other_gin ON otel_log_attrs_other USING gin(attributes)")

    # 6. Spans Fact Table
    op.execute("""
        CREATE TABLE otel_spans_fact (
            span_id BIGSERIAL PRIMARY KEY,
            resource_id BIGINT NOT NULL REFERENCES otel_resources_dim(resource_id),
            scope_id BIGINT REFERENCES otel_scopes_dim(scope_id),

            -- Span identity
            trace_id VARCHAR(32) NOT NULL,
            span_id_hex VARCHAR(16) NOT NULL,
            parent_span_id_hex VARCHAR(16),

            -- Span metadata
            name TEXT NOT NULL,
            kind SMALLINT NOT NULL,

            -- Timing with full nanosecond precision
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            start_time_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            end_time TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time_nanos_fraction SMALLINT NOT NULL DEFAULT 0,

            -- Status
            status_code SMALLINT NOT NULL,
            status_message TEXT,

            -- Attributes catch-all
            attributes_other JSONB,

            -- Events and links as JSONB
            events JSONB,
            links JSONB,

            -- Metadata
            dropped_attributes_count INTEGER NOT NULL DEFAULT 0,
            dropped_events_count INTEGER NOT NULL DEFAULT 0,
            dropped_links_count INTEGER NOT NULL DEFAULT 0,
            flags INTEGER NOT NULL DEFAULT 0
        )""")
    op.execute("CREATE UNIQUE INDEX idx_otel_spans_trace_span ON otel_spans_fact(trace_id, span_id_hex)")
    op.execute("CREATE INDEX idx_otel_spans_trace ON otel_spans_fact(trace_id)")
    op.execute("CREATE INDEX idx_otel_spans_resource ON otel_spans_fact(resource_id)")
    op.execute("CREATE INDEX idx_otel_spans_time ON otel_spans_fact(start_time, start_time_nanos_fraction)")
    op.execute(
        "CREATE INDEX idx_otel_spans_parent ON otel_spans_fact(parent_span_id_hex) WHERE parent_span_id_hex IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_otel_spans_attrs_other_gin ON otel_spans_fact USING gin(attributes_other) WHERE attributes_other IS NOT NULL"
    )
    op.execute("COMMENT ON TABLE otel_spans_fact IS 'Span fact table with timestamp+nanos precision'")

    # 7. Span Attribute Tables
    op.execute("""
        CREATE TABLE otel_span_attrs_string (
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value TEXT NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_string_span ON otel_span_attrs_string(span_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_string_key ON otel_span_attrs_string(key_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_string_value ON otel_span_attrs_string(value)")

    op.execute("""
        CREATE TABLE otel_span_attrs_int (
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BIGINT NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_int_span ON otel_span_attrs_int(span_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_int_key ON otel_span_attrs_int(key_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_int_value ON otel_span_attrs_int(value)")

    op.execute("""
        CREATE TABLE otel_span_attrs_double (
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_double_span ON otel_span_attrs_double(span_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_double_key ON otel_span_attrs_double(key_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_double_value ON otel_span_attrs_double(value)")

    op.execute("""
        CREATE TABLE otel_span_attrs_bool (
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BOOLEAN NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_bool_span ON otel_span_attrs_bool(span_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_bool_key ON otel_span_attrs_bool(key_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_bool_value ON otel_span_attrs_bool(value)")

    op.execute("""
        CREATE TABLE otel_span_attrs_bytes (
            span_id BIGINT NOT NULL REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            key_id BIGINT NOT NULL REFERENCES attribute_keys(key_id),
            value BYTEA NOT NULL,
            PRIMARY KEY (span_id, key_id)
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_bytes_span ON otel_span_attrs_bytes(span_id)")
    op.execute("CREATE INDEX idx_otel_span_attrs_bytes_key ON otel_span_attrs_bytes(key_id)")

    op.execute("""
        CREATE TABLE otel_span_attrs_other (
            span_id BIGINT NOT NULL PRIMARY KEY REFERENCES otel_spans_fact(span_id) ON DELETE CASCADE,
            attributes JSONB NOT NULL
        )""")
    op.execute("CREATE INDEX idx_otel_span_attrs_other_gin ON otel_span_attrs_other USING gin(attributes)")

    # 7b. Add Missing COMMENT Statements
    # Log attribute table comments
    op.execute(
        "COMMENT ON TABLE otel_log_attrs_string IS 'Promoted string log attributes per attribute-promotion.yaml'"
    )
    op.execute("COMMENT ON TABLE otel_log_attrs_int IS 'Promoted integer log attributes per attribute-promotion.yaml'")
    op.execute(
        "COMMENT ON TABLE otel_log_attrs_double IS 'Promoted double log attributes per attribute-promotion.yaml'"
    )
    op.execute("COMMENT ON TABLE otel_log_attrs_bool IS 'Promoted boolean log attributes per attribute-promotion.yaml'")
    op.execute("COMMENT ON TABLE otel_log_attrs_bytes IS 'Promoted bytes log attributes per attribute-promotion.yaml'")
    op.execute(
        "COMMENT ON TABLE otel_log_attrs_other IS 'JSONB catch-all for unpromoted log attributes (complex types)'"
    )

    # Span attribute table comments
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_string IS 'Promoted string span attributes per attribute-promotion.yaml'"
    )
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_int IS 'Promoted integer span attributes per attribute-promotion.yaml'"
    )
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_double IS 'Promoted double span attributes per attribute-promotion.yaml'"
    )
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_bool IS 'Promoted boolean span attributes per attribute-promotion.yaml'"
    )
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_bytes IS 'Promoted bytes span attributes per attribute-promotion.yaml'"
    )
    op.execute(
        "COMMENT ON TABLE otel_span_attrs_other IS 'JSONB catch-all for unpromoted span attributes (complex types)'"
    )

    # Column comments for timestamp nanos_fraction fields
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in time field'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_logs_fact.observed_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in observed_time field'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.start_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in start_time field'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_spans_fact.end_time_nanos_fraction IS 'Remaining nanoseconds (0-999) beyond microsecond precision in end_time field'"
    )

    # Hash field comments
    op.execute(
        "COMMENT ON COLUMN otel_resources_dim.resource_hash IS 'SHA-256 hash of sorted resource attributes for deduplication'"
    )
    op.execute(
        "COMMENT ON COLUMN otel_scopes_dim.scope_hash IS 'SHA-256 hash of scope identity (name+version+schema_url) for deduplication'"
    )

    # 8. Logs Enriched View
    op.execute("""
        CREATE OR REPLACE VIEW v_otel_logs_enriched AS
        WITH log_attrs AS (
            SELECT
                lf.log_id,
                jsonb_object_agg(ak.key, las.value) FILTER (WHERE las.value IS NOT NULL) AS attrs_string,
                jsonb_object_agg(ak.key, lai.value) FILTER (WHERE lai.value IS NOT NULL) AS attrs_int,
                jsonb_object_agg(ak.key, lad.value) FILTER (WHERE lad.value IS NOT NULL) AS attrs_double,
                jsonb_object_agg(ak.key, lab.value) FILTER (WHERE lab.value IS NOT NULL) AS attrs_bool
            FROM otel_logs_fact lf
            LEFT JOIN otel_log_attrs_string las ON lf.log_id = las.log_id
            LEFT JOIN otel_log_attrs_int lai ON lf.log_id = lai.log_id
            LEFT JOIN otel_log_attrs_double lad ON lf.log_id = lad.log_id
            LEFT JOIN otel_log_attrs_bool lab ON lf.log_id = lab.log_id
            LEFT JOIN attribute_keys ak ON ak.key_id IN (las.key_id, lai.key_id, lad.key_id, lab.key_id)
            GROUP BY lf.log_id
        )
        SELECT
            lf.log_id,
            lf.time,
            lf.time_nanos_fraction,
            lf.observed_time,
            lf.observed_time_nanos_fraction,
            lf.severity_number,
            lf.severity_text,
            lf.body,
            lf.trace_id,
            lf.span_id_hex,
            lf.trace_flags,
            lf.resource_id,
            rd.resource_hash,
            rd.service_name,
            rd.service_namespace,
            lf.scope_id,
            sd.scope_hash,
            sd.name AS scope_name,
            sd.version AS scope_version,
            COALESCE(la.attrs_string, '{}'::jsonb) ||
            COALESCE(la.attrs_int, '{}'::jsonb) ||
            COALESCE(la.attrs_double, '{}'::jsonb) ||
            COALESCE(la.attrs_bool, '{}'::jsonb) ||
            COALESCE(lf.attributes_other, '{}'::jsonb) AS attributes
        FROM otel_logs_fact lf
        JOIN otel_resources_dim rd ON lf.resource_id = rd.resource_id
        LEFT JOIN otel_scopes_dim sd ON lf.scope_id = sd.scope_id
        LEFT JOIN log_attrs la ON lf.log_id = la.log_id""")
    op.execute("COMMENT ON VIEW v_otel_logs_enriched IS 'Enriched logs view with all attributes aggregated'")

    # 9. Spans Enriched View
    op.execute("""
        CREATE OR REPLACE VIEW v_otel_spans_enriched AS
        WITH span_attrs AS (
            SELECT
                sf.span_id,
                jsonb_object_agg(ak.key, sas.value) FILTER (WHERE sas.value IS NOT NULL) AS attrs_string,
                jsonb_object_agg(ak.key, sai.value) FILTER (WHERE sai.value IS NOT NULL) AS attrs_int,
                jsonb_object_agg(ak.key, sad.value) FILTER (WHERE sad.value IS NOT NULL) AS attrs_double,
                jsonb_object_agg(ak.key, sab.value) FILTER (WHERE sab.value IS NOT NULL) AS attrs_bool
            FROM otel_spans_fact sf
            LEFT JOIN otel_span_attrs_string sas ON sf.span_id = sas.span_id
            LEFT JOIN otel_span_attrs_int sai ON sf.span_id = sai.span_id
            LEFT JOIN otel_span_attrs_double sad ON sf.span_id = sad.span_id
            LEFT JOIN otel_span_attrs_bool sab ON sf.span_id = sab.span_id
            LEFT JOIN attribute_keys ak ON ak.key_id IN (sas.key_id, sai.key_id, sad.key_id, sab.key_id)
            GROUP BY sf.span_id
        )
        SELECT
            sf.span_id,
            sf.trace_id,
            sf.span_id_hex,
            sf.parent_span_id_hex,
            sf.name,
            sf.kind,
            sf.start_time,
            sf.start_time_nanos_fraction,
            sf.end_time,
            sf.end_time_nanos_fraction,
            sf.status_code,
            sf.status_message,
            sf.resource_id,
            rd.resource_hash,
            rd.service_name,
            rd.service_namespace,
            sf.scope_id,
            sd.scope_hash,
            sd.name AS scope_name,
            sd.version AS scope_version,
            sf.events,
            sf.links,
            COALESCE(sa.attrs_string, '{}'::jsonb) ||
            COALESCE(sa.attrs_int, '{}'::jsonb) ||
            COALESCE(sa.attrs_double, '{}'::jsonb) ||
            COALESCE(sa.attrs_bool, '{}'::jsonb) ||
            COALESCE(sf.attributes_other, '{}'::jsonb) AS attributes
        FROM otel_spans_fact sf
        JOIN otel_resources_dim rd ON sf.resource_id = rd.resource_id
        LEFT JOIN otel_scopes_dim sd ON sf.scope_id = sd.scope_id
        LEFT JOIN span_attrs sa ON sf.span_id = sa.span_id""")
    op.execute("COMMENT ON VIEW v_otel_spans_enriched IS 'Enriched spans view with all attributes aggregated'")


def downgrade() -> None:
    """Drop all OTLP schema objects."""
    op.execute("DROP VIEW IF EXISTS v_otel_spans_enriched CASCADE")
    op.execute("DROP VIEW IF EXISTS v_otel_logs_enriched CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_span_attrs_string CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_spans_fact CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_log_attrs_string CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_logs_fact CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scope_attrs_string CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_scopes_dim CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_other CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_bytes CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_bool CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_double CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_int CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resource_attrs_string CASCADE")
    op.execute("DROP TABLE IF EXISTS otel_resources_dim CASCADE")
    op.execute("DROP TABLE IF EXISTS aggregation_temporalities CASCADE")
    op.execute("DROP TABLE IF EXISTS metric_types CASCADE")
    op.execute("DROP TABLE IF EXISTS status_codes CASCADE")
    op.execute("DROP TABLE IF EXISTS span_kinds CASCADE")
    op.execute("DROP TABLE IF EXISTS log_body_types CASCADE")
    op.execute("DROP TABLE IF EXISTS log_severity_numbers CASCADE")
    op.execute("DROP TABLE IF EXISTS attribute_keys CASCADE")
