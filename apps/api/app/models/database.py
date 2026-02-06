"""SQLAlchemy ORM models for PostgreSQL schema.

These models provide type-safe, validated mappings to the database tables,
eliminating manual SQL construction and field mapping errors.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ServiceDim(Base):
    """Service catalog (dimension table).

    Service name is globally unique. Namespace info stored in resource attributes.
    All fact tables reference this via service_id FK.
    """

    __tablename__ = "service_dim"
    __table_args__ = (Index("idx_service_name", "name", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    version: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    first_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class OperationDim(Base):
    """Operation (span name) catalog (dimension table)."""

    __tablename__ = "operation_dim"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("service_dim.id"), nullable=True, default=None)
    name: Mapped[str] = mapped_column(String(1024))
    span_kind: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, default=None)
    first_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class ResourceDim(Base):
    """Resource attributes catalog (dimension table)."""

    __tablename__ = "resource_dim"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_hash: Mapped[str] = mapped_column(String(64))
    attributes: Mapped[dict] = mapped_column(JSONB)
    first_seen: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_seen: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class SpansFact(Base):
    """Span fact table (partitioned by start_time_unix_nano)."""

    __tablename__ = "spans_fact"
    __table_args__ = (
        Index("idx_spans_trace_id", "trace_id"),
        Index("idx_spans_service", "service_id"),
        Index("idx_spans_time", "start_timestamp", "start_nanos_fraction", "id"),
        Index("idx_spans_span_id", "span_id"),
        Index("idx_spans_attributes", "attributes", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32))
    span_id: Mapped[str] = mapped_column(String(16))
    parent_span_id: Mapped[str | None] = mapped_column(String(16), nullable=True, default=None)

    # Core OTEL fields
    name: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[int] = mapped_column(SmallInteger)
    status_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, default=None)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    start_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    start_nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)
    end_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    end_nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)
    # duration is GENERATED column, not included in model

    # References
    service_id: Mapped[int | None] = mapped_column(ForeignKey("service_dim.id"), nullable=True, default=None)
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("operation_dim.id"), nullable=True, default=None)
    resource_id: Mapped[int | None] = mapped_column(ForeignKey("resource_dim.id"), nullable=True, default=None)

    # OTEL structures as JSONB
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    events: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    links: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    resource: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Flags
    flags: Mapped[int] = mapped_column(Integer, default=0)
    dropped_attributes_count: Mapped[int] = mapped_column(Integer, default=0)
    dropped_events_count: Mapped[int] = mapped_column(Integer, default=0)
    dropped_links_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class LogsFact(Base):
    """Log fact table (partitioned by time_unix_nano)."""

    __tablename__ = "logs_fact"
    __table_args__ = (
        Index("idx_logs_trace_id", "trace_id"),
        Index("idx_logs_time", "timestamp", "nanos_fraction", "id"),
        Index("idx_logs_severity", "severity_number"),
        Index("idx_logs_attributes", "attributes", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # OTEL correlation
    trace_id: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    span_id: Mapped[str | None] = mapped_column(String(16), nullable=True, default=None)

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)
    observed_timestamp: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=None)
    observed_nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Severity
    severity_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, default=None)
    severity_text: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)

    # Content
    body: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # References
    service_id: Mapped[int | None] = mapped_column(ForeignKey("service_dim.id"), nullable=True, default=None)

    # OTEL structures
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    resource: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Flags
    flags: Mapped[int] = mapped_column(Integer, default=0)
    dropped_attributes_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class MetricsFact(Base):
    """Metric fact table (partitioned by time_unix_nano).

    Schema matches the Alembic migration (29f08ce99e6e).
    """

    __tablename__ = "metrics_fact"
    __table_args__ = (
        Index("idx_metrics_time", "timestamp", "nanos_fraction", "id"),
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_attributes", "attributes", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)
    start_timestamp: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True, default=None)
    start_nanos_fraction: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Metric identity
    metric_name: Mapped[str] = mapped_column(String(1024))
    metric_type: Mapped[str] = mapped_column(String(32))
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # References
    service_id: Mapped[int | None] = mapped_column(ForeignKey("service_dim.id"), nullable=True, default=None)

    # OTEL structures (stored as JSONB in database)
    resource: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    data_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Aggregation metadata
    temporality: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    is_monotonic: Mapped[bool | None] = mapped_column(nullable=True, default=None)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
