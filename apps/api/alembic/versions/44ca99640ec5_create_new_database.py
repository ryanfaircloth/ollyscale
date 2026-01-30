"""create new database

Revision ID: 44ca99640ec5
Revises:
Create Date: 2026-01-25 18:26:09.708370

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "44ca99640ec5"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial schema with TIMESTAMP + nanos_fraction columns."""

    # tenant_dim - Tenant catalog (multi-tenancy support)
    op.execute("""
        CREATE TABLE tenant_dim (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    # Seed with unknown tenant
    op.execute("INSERT INTO tenant_dim (id, name) VALUES (1, 'unknown')")

    # connection_dim - Connection catalog (tracks data sources)
    op.execute("""
        CREATE TABLE connection_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL REFERENCES tenant_dim(id),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    # Seed with unknown connection
    op.execute("INSERT INTO connection_dim (id, tenant_id, name) VALUES (1, 1, 'unknown')")

    # namespace_dim - NOTE: namespace field is nullable (not NOT NULL)
    # NULLS NOT DISTINCT ensures only one NULL namespace per tenant (PostgreSQL 15+)
    op.execute("""
        CREATE TABLE namespace_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            namespace VARCHAR(255),
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            UNIQUE NULLS NOT DISTINCT (tenant_id, namespace)
        )
    """)

    # service_dim
    op.execute("""
        CREATE TABLE service_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            name VARCHAR(255) NOT NULL,
            namespace_id INTEGER REFERENCES namespace_dim(id),
            version VARCHAR(255),
            attributes JSONB,
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.create_index("idx_service_name_namespace", "service_dim", ["name", "namespace_id"], unique=True)

    # operation_dim
    op.execute("""
        CREATE TABLE operation_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            service_id INTEGER REFERENCES service_dim(id),
            name VARCHAR(1024) NOT NULL,
            span_kind SMALLINT,
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            UNIQUE(tenant_id, service_id, name, span_kind)
        )
    """)

    # resource_dim
    op.execute("""
        CREATE TABLE resource_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            resource_hash VARCHAR(64) NOT NULL,
            attributes JSONB NOT NULL,
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            UNIQUE(tenant_id, resource_hash)
        )
    """)

    # spans_fact
    op.execute("""
        CREATE TABLE spans_fact (
            id BIGSERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id),
            trace_id VARCHAR(32) NOT NULL,
            span_id VARCHAR(16) NOT NULL,
            parent_span_id VARCHAR(16),
            name VARCHAR(1024) NOT NULL,
            kind SMALLINT NOT NULL,
            status_code SMALLINT,
            status_message TEXT,
            start_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            start_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            end_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            end_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            service_id INTEGER REFERENCES service_dim(id),
            operation_id INTEGER REFERENCES operation_dim(id),
            resource_id INTEGER REFERENCES resource_dim(id),
            attributes JSONB,
            events JSONB,
            links JSONB,
            resource JSONB,
            scope JSONB,
            flags INTEGER DEFAULT 0,
            dropped_attributes_count INTEGER DEFAULT 0,
            dropped_events_count INTEGER DEFAULT 0,
            dropped_links_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.create_index("idx_spans_trace_id", "spans_fact", ["trace_id"])
    op.create_index("idx_spans_service", "spans_fact", ["service_id"])
    op.create_index("idx_spans_time", "spans_fact", ["start_timestamp", "start_nanos_fraction", "id"])
    op.create_index("idx_spans_span_id", "spans_fact", ["span_id"])
    op.create_index("idx_spans_attributes", "spans_fact", ["attributes"], postgresql_using="gin")

    # logs_fact
    op.execute("""
        CREATE TABLE logs_fact (
            id BIGSERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id),
            trace_id VARCHAR(32),
            span_id VARCHAR(16),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            observed_timestamp TIMESTAMP WITH TIME ZONE,
            observed_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            severity_number SMALLINT,
            severity_text VARCHAR(64),
            body JSONB,
            service_id INTEGER REFERENCES service_dim(id),
            attributes JSONB,
            resource JSONB,
            scope JSONB,
            flags INTEGER DEFAULT 0,
            dropped_attributes_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.create_index("idx_logs_trace_id", "logs_fact", ["trace_id"])
    op.create_index("idx_logs_time", "logs_fact", ["timestamp", "nanos_fraction", "id"])
    op.create_index("idx_logs_severity", "logs_fact", ["severity_number"])
    op.create_index("idx_logs_attributes", "logs_fact", ["attributes"], postgresql_using="gin")

    # metrics_fact
    op.execute("""
        CREATE TABLE metrics_fact (
            id BIGSERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
            connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            start_timestamp TIMESTAMP WITH TIME ZONE,
            start_nanos_fraction SMALLINT NOT NULL DEFAULT 0,
            metric_name VARCHAR(1024) NOT NULL,
            metric_type VARCHAR(32) NOT NULL,
            unit VARCHAR(64),
            description TEXT,
            service_id INTEGER REFERENCES service_dim(id),
            resource JSONB,
            scope JSONB,
            attributes JSONB,
            data_points JSONB,
            temporality VARCHAR(32),
            is_monotonic BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.create_index("idx_metrics_time", "metrics_fact", ["timestamp", "nanos_fraction", "id"])
    op.create_index("idx_metrics_name", "metrics_fact", ["metric_name"])
    op.create_index("idx_metrics_attributes", "metrics_fact", ["attributes"], postgresql_using="gin")


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("metrics_fact")
    op.drop_table("logs_fact")
    op.drop_table("spans_fact")
    op.drop_table("resource_dim")
    op.drop_table("operation_dim")
    op.drop_table("service_dim")
    op.drop_table("namespace_dim")
    op.drop_table("connection_dim")
    op.drop_table("tenant_dim")
