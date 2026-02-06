"""remove tenant and connection fields

Revision ID: a1b2c3d4e5f6
Revises: 44ca99640ec5
Create Date: 2026-02-05 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "44ca99640ec5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove tenant_id and connection_id columns and related tables.

    These fields were always hardcoded to 'unknown' values and never used
    for actual multi-tenancy, so removing them simplifies the schema.
    """

    # Drop connection_id and tenant_id from fact tables
    op.drop_column("spans_fact", "connection_id")
    op.drop_column("spans_fact", "tenant_id")

    op.drop_column("logs_fact", "connection_id")
    op.drop_column("logs_fact", "tenant_id")

    op.drop_column("metrics_fact", "connection_id")
    op.drop_column("metrics_fact", "tenant_id")

    # Drop the old unique constraint on (tenant_id, namespace) before dropping tenant_id
    op.execute("ALTER TABLE namespace_dim DROP CONSTRAINT IF EXISTS namespace_dim_tenant_id_namespace_key")

    # Drop the old unique constraint on service_dim before dropping namespace_id
    op.execute("ALTER TABLE service_dim DROP CONSTRAINT IF EXISTS idx_service_name_namespace")

    # Drop the old unique constraint on (tenant_id, service_id, name, span_kind) before dropping tenant_id
    op.execute(
        "ALTER TABLE operation_dim DROP CONSTRAINT IF EXISTS operation_dim_tenant_id_service_id_name_span_kind_key"
    )

    # Drop the old unique constraint on (tenant_id, resource_hash) before dropping tenant_id
    op.execute("ALTER TABLE resource_dim DROP CONSTRAINT IF EXISTS resource_dim_tenant_id_resource_hash_key")

    # Drop tenant_id from dimension tables
    op.drop_column("namespace_dim", "tenant_id")
    op.drop_column("service_dim", "tenant_id")
    op.drop_column("operation_dim", "tenant_id")
    op.drop_column("resource_dim", "tenant_id")

    # Drop namespace_id from service_dim (namespace is just a resource attribute now)
    op.drop_column("service_dim", "namespace_id")

    # Add new unique constraints
    op.execute("ALTER TABLE service_dim ADD CONSTRAINT service_dim_name_key UNIQUE (name)")
    op.execute(
        "ALTER TABLE operation_dim ADD CONSTRAINT operation_dim_service_id_name_span_kind_key UNIQUE (service_id, name, span_kind)"
    )
    op.execute("ALTER TABLE resource_dim ADD CONSTRAINT resource_dim_resource_hash_key UNIQUE (resource_hash)")

    # Drop the catalog tables (no longer needed - namespace is just a resource attribute)
    op.drop_table("connection_dim")
    op.drop_table("tenant_dim")
    op.drop_table("namespace_dim")


def downgrade() -> None:
    """Recreate tenant_id and connection_id columns and related tables.

    This allows rollback if needed, recreating the multi-tenancy infrastructure
    with default 'unknown' values.
    """

    # Recreate namespace_dim table
    op.execute("""
        CREATE TABLE namespace_dim (
            id SERIAL PRIMARY KEY,
            namespace VARCHAR(255) UNIQUE,
            first_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.execute("INSERT INTO namespace_dim (id, namespace) VALUES (1, NULL)")

    # Recreate tenant_dim table
    op.execute("""
        CREATE TABLE tenant_dim (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.execute("INSERT INTO tenant_dim (id, name) VALUES (1, 'unknown')")

    # Recreate connection_dim table
    op.execute("""
        CREATE TABLE connection_dim (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER NOT NULL REFERENCES tenant_dim(id),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.execute("INSERT INTO connection_dim (id, tenant_id, name) VALUES (1, 1, 'unknown')")

    # Drop the new unique constraints before adding tenant_id back
    op.execute("ALTER TABLE service_dim DROP CONSTRAINT IF EXISTS service_dim_name_key")
    op.execute("ALTER TABLE operation_dim DROP CONSTRAINT IF EXISTS operation_dim_service_id_name_span_kind_key")
    op.execute("ALTER TABLE resource_dim DROP CONSTRAINT IF EXISTS resource_dim_resource_hash_key")

    # Add tenant_id back to dimension tables
    op.execute("""
        ALTER TABLE namespace_dim
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id)
    """)

    # Add namespace_id back to service_dim
    op.execute("""
        ALTER TABLE service_dim
        ADD COLUMN namespace_id INTEGER DEFAULT 1 REFERENCES namespace_dim(id),
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id)
    """)

    op.execute("""
        ALTER TABLE operation_dim
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id)
    """)

    op.execute("""
        ALTER TABLE resource_dim
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id)
    """)

    # Recreate the old unique constraints with tenant_id and namespace_id
    op.execute(
        "ALTER TABLE namespace_dim ADD CONSTRAINT namespace_dim_tenant_id_namespace_key UNIQUE NULLS NOT DISTINCT (tenant_id, namespace)"
    )
    op.execute("CREATE UNIQUE INDEX idx_service_name_namespace ON service_dim (name, namespace_id)")
    op.execute(
        "ALTER TABLE operation_dim ADD CONSTRAINT operation_dim_tenant_id_service_id_name_span_kind_key UNIQUE (tenant_id, service_id, name, span_kind)"
    )
    op.execute(
        "ALTER TABLE resource_dim ADD CONSTRAINT resource_dim_tenant_id_resource_hash_key UNIQUE (tenant_id, resource_hash)"
    )

    # Add tenant_id and connection_id back to fact tables
    op.execute("""
        ALTER TABLE spans_fact
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
        ADD COLUMN connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id)
    """)

    op.execute("""
        ALTER TABLE logs_fact
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
        ADD COLUMN connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id)
    """)

    op.execute("""
        ALTER TABLE metrics_fact
        ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES tenant_dim(id),
        ADD COLUMN connection_id INTEGER NOT NULL DEFAULT 1 REFERENCES connection_dim(id)
    """)
