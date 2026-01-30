"""SQLModel ORM models for PostgreSQL schema.

These models provide type-safe, validated mappings to the database tables,
eliminating manual SQL construction and field mapping errors.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, Index, Integer, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, SQLModel


class TenantDim(SQLModel, table=True):
    """Tenant catalog (dimension table).

    Multi-tenancy support. Seeded with id=1, name='unknown'.
    """

    __tablename__ = "tenant_dim"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConnectionDim(SQLModel, table=True):
    """Connection catalog (dimension table).

    Tracks data sources. Seeded with id=1, tenant_id=1, name='unknown'.
    """

    __tablename__ = "connection_dim"

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    name: str = Field(max_length=255, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NamespaceDim(SQLModel, table=True):
    """Namespace catalog (dimension table).

    Namespaces contain services. A NULL namespace represents services without a namespace.
    Seeded with id=1, namespace=NULL.
    """

    __tablename__ = "namespace_dim"

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    namespace: str | None = Field(default=None, max_length=255, unique=True)
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceDim(SQLModel, table=True):
    """Service catalog (dimension table).

    Service name is unique within a namespace (UNIQUE(name, namespace_id)).
    All fact tables reference this via service_id FK.
    """

    __tablename__ = "service_dim"
    __table_args__ = (Index("idx_service_name_namespace", "name", "namespace_id", unique=True),)

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    name: str = Field(max_length=255, nullable=False)
    namespace_id: int | None = Field(default=None, foreign_key="namespace_dim.id")
    version: str | None = Field(default=None, max_length=255)
    attributes: dict | None = Field(default=None, sa_column=Column(JSONB))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OperationDim(SQLModel, table=True):
    """Operation (span name) catalog (dimension table)."""

    __tablename__ = "operation_dim"

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    service_id: int | None = Field(default=None, foreign_key="service_dim.id")
    name: str = Field(max_length=1024, nullable=False)
    span_kind: int | None = Field(default=None, sa_column=Column(SmallInteger))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResourceDim(SQLModel, table=True):
    """Resource attributes catalog (dimension table)."""

    __tablename__ = "resource_dim"

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    resource_hash: str = Field(max_length=64, nullable=False)
    attributes: dict = Field(sa_column=Column(JSONB, nullable=False))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class SpansFact(SQLModel, table=True):
    """Span fact table (partitioned by start_time_unix_nano)."""

    __tablename__ = "spans_fact"
    __table_args__ = (
        Index("idx_spans_trace_id", "trace_id"),
        Index("idx_spans_service", "service_id"),
        Index("idx_spans_time", "start_timestamp", "start_nanos_fraction", "id"),
        Index("idx_spans_span_id", "span_id"),
        Index("idx_spans_attributes", "attributes", postgresql_using="gin"),
    )

    id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    connection_id: int = Field(default=1, foreign_key="connection_dim.id", nullable=False)
    trace_id: str = Field(max_length=32, nullable=False)
    span_id: str = Field(max_length=16, nullable=False)
    parent_span_id: str | None = Field(default=None, max_length=16)

    # Core OTEL fields
    name: str = Field(max_length=1024, nullable=False)
    kind: int = Field(sa_column=Column(SmallInteger, nullable=False))
    status_code: int | None = Field(default=None, sa_column=Column(SmallInteger))
    status_message: str | None = Field(default=None, sa_column=Column(Text))

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    start_timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    start_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    end_timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    end_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    # duration is GENERATED column, not included in model

    # References
    service_id: int | None = Field(default=None, foreign_key="service_dim.id")
    operation_id: int | None = Field(default=None, foreign_key="operation_dim.id")
    resource_id: int | None = Field(default=None, foreign_key="resource_dim.id")

    # OTEL structures as JSONB
    attributes: dict | None = Field(default=None, sa_column=Column(JSONB))
    events: dict | None = Field(default=None, sa_column=Column(JSONB))
    links: dict | None = Field(default=None, sa_column=Column(JSONB))
    resource: dict | None = Field(default=None, sa_column=Column(JSONB))
    scope: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Flags
    flags: int = Field(default=0, sa_column=Column(Integer))
    dropped_attributes_count: int = Field(default=0, sa_column=Column(Integer))
    dropped_events_count: int = Field(default=0, sa_column=Column(Integer))
    dropped_links_count: int = Field(default=0, sa_column=Column(Integer))

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LogsFact(SQLModel, table=True):
    """Log fact table (partitioned by time_unix_nano)."""

    __tablename__ = "logs_fact"
    __table_args__ = (
        Index("idx_logs_trace_id", "trace_id"),
        Index("idx_logs_time", "timestamp", "nanos_fraction", "id"),
        Index("idx_logs_severity", "severity_number"),
        Index("idx_logs_attributes", "attributes", postgresql_using="gin"),
    )

    id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    connection_id: int = Field(default=1, foreign_key="connection_dim.id", nullable=False)

    # OTEL correlation
    trace_id: str | None = Field(default=None, max_length=32)
    span_id: str | None = Field(default=None, max_length=16)

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    observed_timestamp: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    observed_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))

    # Severity
    severity_number: int | None = Field(default=None, sa_column=Column(SmallInteger))
    severity_text: str | None = Field(default=None, max_length=64)

    # Content
    body: dict | None = Field(default=None, sa_column=Column(JSONB))

    # References
    service_id: int | None = Field(default=None, foreign_key="service_dim.id")

    # OTEL structures
    attributes: dict | None = Field(default=None, sa_column=Column(JSONB))
    resource: dict | None = Field(default=None, sa_column=Column(JSONB))
    scope: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Flags
    flags: int = Field(default=0, sa_column=Column(Integer))
    dropped_attributes_count: int = Field(default=0, sa_column=Column(Integer))

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MetricsFact(SQLModel, table=True):
    """Metric fact table (partitioned by time_unix_nano).

    Schema matches the Alembic migration (29f08ce99e6e).
    """

    __tablename__ = "metrics_fact"
    __table_args__ = (
        Index("idx_metrics_time", "timestamp", "nanos_fraction", "id"),
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_attributes", "attributes", postgresql_using="gin"),
    )

    id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    tenant_id: int = Field(default=1, foreign_key="tenant_dim.id", nullable=False)
    connection_id: int = Field(default=1, foreign_key="connection_dim.id", nullable=False)

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    start_timestamp: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    start_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))

    # Metric identity
    metric_name: str = Field(max_length=1024, nullable=False)
    metric_type: str = Field(max_length=32, nullable=False)
    unit: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, sa_column=Column(Text))

    # References
    service_id: int | None = Field(default=None, foreign_key="service_dim.id")

    # OTEL structures (stored as JSONB in database)
    resource: dict | None = Field(default=None, sa_column=Column(JSONB))
    scope: dict | None = Field(default=None, sa_column=Column(JSONB))
    attributes: dict | None = Field(default=None, sa_column=Column(JSONB))
    data_points: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Aggregation metadata
    temporality: str | None = Field(default=None, max_length=32)
    is_monotonic: bool | None = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
