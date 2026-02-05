"""SQLModel ORM models for new OTLP-aligned PostgreSQL schema.

These models map to the denormalized attribute table structure with:
- Separate resource/scope dimension tables
- Typed attribute tables (string, int, double, bool, bytes, other)
- Attribute key registry for deduplication

Timestamp pattern:
- TIMESTAMP WITH TIME ZONE (microsecond precision) + nanos_fraction (0-999)
- Full nanosecond precision maintained for OTLP compatibility
"""

from datetime import UTC, datetime

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Double,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class AttributeKey(SQLModel, table=True):
    """Attribute key registry for deduplication across all signals."""

    __tablename__ = "attribute_keys"
    __table_args__ = (Index("idx_attribute_keys_key", "key", unique=True),)

    key_id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    key: str = Field(max_length=255, nullable=False, unique=True)


class OtelResourcesDim(SQLModel, table=True):
    """Resource dimension table with hash-based deduplication."""

    __tablename__ = "otel_resources_dim"
    __table_args__ = (
        Index("idx_otel_resources_hash", "resource_hash", unique=True),
        Index("idx_otel_resources_service", "service_name", "service_namespace"),
        Index("idx_otel_resources_last_seen", "last_seen"),
    )

    resource_id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    resource_hash: str = Field(max_length=64, nullable=False, unique=True)  # SHA-256 hash
    service_name: str | None = Field(default=None, max_length=255)
    service_namespace: str | None = Field(default=None, max_length=255)
    schema_url: str | None = Field(default=None, sa_column=Column(Text))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    dropped_attributes_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))


class OtelScopesDim(SQLModel, table=True):
    """Instrumentation scope (library) dimension table."""

    __tablename__ = "otel_scopes_dim"
    __table_args__ = (
        Index("idx_otel_scopes_hash", "scope_hash", unique=True),
        Index("idx_otel_scopes_name", "name"),
        Index("idx_otel_scopes_last_seen", "last_seen"),
    )

    scope_id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    scope_hash: str = Field(max_length=64, nullable=False, unique=True)  # SHA-256 hash
    name: str = Field(max_length=255, nullable=False)
    version: str | None = Field(default=None, max_length=255)
    schema_url: str | None = Field(default=None, sa_column=Column(Text))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)
    dropped_attributes_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))


class OtelLogsFact(SQLModel, table=True):
    """Log fact table with OTLP schema (new denormalized structure)."""

    __tablename__ = "otel_logs_fact"
    __table_args__ = (
        Index("idx_otel_logs_time", "time", "time_nanos_fraction"),
        Index("idx_otel_logs_resource", "resource_id"),
        Index("idx_otel_logs_severity", "severity_number"),
        Index("idx_otel_logs_trace", "trace_id", "span_id_hex"),
    )

    log_id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))

    # Resource and scope references
    resource_id: int = Field(sa_column=Column(BigInteger, ForeignKey("otel_resources_dim.resource_id"), nullable=False))
    scope_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, ForeignKey("otel_scopes_dim.scope_id"), nullable=True)
    )

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    time_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    observed_time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    observed_time_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))

    # Severity
    severity_number: int | None = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    severity_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Body
    body_type_id: int | None = Field(default=None, sa_column=Column(SmallInteger, nullable=True))
    body: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Trace correlation (optional)
    trace_id: str | None = Field(default=None, max_length=32, nullable=True)
    span_id_hex: str | None = Field(default=None, max_length=16, nullable=True)
    trace_flags: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))

    # Attributes
    attributes_other: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )  # Non-promoted attributes

    # Metadata
    dropped_attributes_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    flags: int = Field(default=0, sa_column=Column(Integer, nullable=False))


# Attribute tables


class OtelLogAttrsString(SQLModel, table=True):
    """String-typed log attributes."""

    __tablename__ = "otel_log_attrs_string"
    __table_args__ = (
        Index("idx_otel_log_attrs_string_log", "log_id"),
        Index("idx_otel_log_attrs_string_key", "key_id"),
        Index("idx_otel_log_attrs_string_value", "value"),
    )

    log_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: str = Field(sa_column=Column(Text, nullable=False))


class OtelLogAttrsInt(SQLModel, table=True):
    """Integer-typed log attributes."""

    __tablename__ = "otel_log_attrs_int"
    __table_args__ = (
        Index("idx_otel_log_attrs_int_log", "log_id"),
        Index("idx_otel_log_attrs_int_key", "key_id"),
        Index("idx_otel_log_attrs_int_value", "value"),
    )

    log_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: int = Field(sa_column=Column(BigInteger, nullable=False))


class OtelLogAttrsDouble(SQLModel, table=True):
    """Double precision floating point log attributes."""

    __tablename__ = "otel_log_attrs_double"
    __table_args__ = (
        Index("idx_otel_log_attrs_double_log", "log_id"),
        Index("idx_otel_log_attrs_double_key", "key_id"),
        Index("idx_otel_log_attrs_double_value", "value"),
    )

    log_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: float = Field(sa_column=Column(Double, nullable=False))


class OtelLogAttrsBool(SQLModel, table=True):
    """Boolean-typed log attributes."""

    __tablename__ = "otel_log_attrs_bool"
    __table_args__ = (
        Index("idx_otel_log_attrs_bool_log", "log_id"),
        Index("idx_otel_log_attrs_bool_key", "key_id"),
        Index("idx_otel_log_attrs_bool_value", "value"),
    )

    log_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: bool = Field(sa_column=Column(Boolean, nullable=False))


class OtelLogAttrsBytes(SQLModel, table=True):
    """Binary/bytes log attributes."""

    __tablename__ = "otel_log_attrs_bytes"
    __table_args__ = (
        Index("idx_otel_log_attrs_bytes_log", "log_id"),
        Index("idx_otel_log_attrs_bytes_key", "key_id"),
    )

    log_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: bytes = Field(sa_column=Column(LargeBinary, nullable=False))


class OtelLogAttrsOther(SQLModel, table=True):
    """JSONB catch-all for complex/array log attributes."""

    __tablename__ = "otel_log_attrs_other"
    __table_args__ = (Index("idx_otel_log_attrs_other_gin", "attributes", postgresql_using="gin"),)

    log_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("otel_logs_fact.log_id", ondelete="CASCADE"), primary_key=True, nullable=False
        )
    )
    attributes: dict = Field(sa_column=Column(JSONB, nullable=False))


# Spans


class OtelSpansFact(SQLModel, table=True):
    """Span fact table with OTLP schema (new denormalized structure)."""

    __tablename__ = "otel_spans_fact"
    __table_args__ = (
        Index("idx_otel_spans_trace_span", "trace_id", "span_id_hex", unique=True),
        Index("idx_otel_spans_trace", "trace_id"),
        Index("idx_otel_spans_resource", "resource_id"),
        Index("idx_otel_spans_time", "start_time", "start_time_nanos_fraction"),
        Index("idx_otel_spans_parent", "parent_span_id_hex"),
    )

    span_id: int | None = Field(default=None, sa_column=Column(BigInteger, primary_key=True))

    # Resource and scope references
    resource_id: int = Field(sa_column=Column(BigInteger, ForeignKey("otel_resources_dim.resource_id"), nullable=False))
    scope_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, ForeignKey("otel_scopes_dim.scope_id"), nullable=True)
    )

    # Span identity
    trace_id: str = Field(max_length=32, nullable=False)
    span_id_hex: str = Field(max_length=16, nullable=False)
    parent_span_id_hex: str | None = Field(default=None, max_length=16, nullable=True)

    # Span details
    name: str = Field(sa_column=Column(Text, nullable=False))
    kind: int = Field(sa_column=Column(SmallInteger, nullable=False))  # SpanKind enum

    # Timing - TIMESTAMP (microsecond precision) + nanos_fraction (0-999) for full nanosecond precision
    start_time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    start_time_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))
    end_time: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    end_time_nanos_fraction: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False))

    # Status
    status_code: int = Field(sa_column=Column(SmallInteger, nullable=False))  # StatusCode enum
    status_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Attributes
    attributes_other: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Metadata
    flags: int = Field(default=0, sa_column=Column(Integer, nullable=False))


# Span attribute tables


class OtelSpanAttrsString(SQLModel, table=True):
    """String-typed span attributes."""

    __tablename__ = "otel_span_attrs_string"
    __table_args__ = (
        Index("idx_otel_span_attrs_string_span", "span_id"),
        Index("idx_otel_span_attrs_string_key", "key_id"),
        Index("idx_otel_span_attrs_string_value", "value"),
    )

    span_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: str = Field(sa_column=Column(Text, nullable=False))


class OtelSpanAttrsInt(SQLModel, table=True):
    """Integer-typed span attributes."""

    __tablename__ = "otel_span_attrs_int"
    __table_args__ = (
        Index("idx_otel_span_attrs_int_span", "span_id"),
        Index("idx_otel_span_attrs_int_key", "key_id"),
        Index("idx_otel_span_attrs_int_value", "value"),
    )

    span_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: int = Field(sa_column=Column(BigInteger, nullable=False))


class OtelSpanAttrsDouble(SQLModel, table=True):
    """Double precision floating point span attributes."""

    __tablename__ = "otel_span_attrs_double"
    __table_args__ = (
        Index("idx_otel_span_attrs_double_span", "span_id"),
        Index("idx_otel_span_attrs_double_key", "key_id"),
        Index("idx_otel_span_attrs_double_value", "value"),
    )

    span_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: float = Field(sa_column=Column(Double, nullable=False))


class OtelSpanAttrsBool(SQLModel, table=True):
    """Boolean-typed span attributes."""

    __tablename__ = "otel_span_attrs_bool"
    __table_args__ = (
        Index("idx_otel_span_attrs_bool_span", "span_id"),
        Index("idx_otel_span_attrs_bool_key", "key_id"),
        Index("idx_otel_span_attrs_bool_value", "value"),
    )

    span_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: bool = Field(sa_column=Column(Boolean, nullable=False))


class OtelSpanAttrsBytes(SQLModel, table=True):
    """Binary/bytes span attributes."""

    __tablename__ = "otel_span_attrs_bytes"
    __table_args__ = (
        Index("idx_otel_span_attrs_bytes_span", "span_id"),
        Index("idx_otel_span_attrs_bytes_key", "key_id"),
    )

    span_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True)
    )
    key_id: int = Field(sa_column=Column(BigInteger, ForeignKey("attribute_keys.key_id"), primary_key=True))
    value: bytes = Field(sa_column=Column(LargeBinary, nullable=False))


class OtelSpanAttrsOther(SQLModel, table=True):
    """JSONB catch-all for complex/array span attributes."""

    __tablename__ = "otel_span_attrs_other"
    __table_args__ = (Index("idx_otel_span_attrs_other_gin", "attributes", postgresql_using="gin"),)

    span_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("otel_spans_fact.span_id", ondelete="CASCADE"), primary_key=True, nullable=False
        )
    )
    attributes: dict = Field(sa_column=Column(JSONB, nullable=False))
