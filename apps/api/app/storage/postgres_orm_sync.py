"""PostgreSQL storage implementation using SQLModel ORM (SYNC VERSION).

This is the synchronous version using psycopg2 instead of asyncpg.
Uses ThreadPoolExecutor for concurrent operations instead of async/await.

This replaces raw SQL construction with type-safe ORM operations.
No more field name mismatches or manual SQL string building.

Transaction Strategy:
--------------------
**DIMENSION UPSERTS** (namespace, service, operation, resource):
- Use AUTOCOMMIT mode - each upsert commits immediately
- Idempotent - safe for concurrent multi-process execution
- No explicit BEGIN/COMMIT - queries execute and commit atomically
- Use RETURNING clause to get IDs without separate SELECT

**FACT INSERTS** (spans, logs, metrics):
- Use EXPLICIT TRANSACTION after dimensions are committed
- All fact rows inserted in single transaction (can rollback if error)
- Separate session from dimension upserts

Why this matters:
- Dimension upserts MUST be idempotent for multi-process safety (no transaction locking)
- Each dimension commit makes data visible to all processes immediately
- Fact inserts benefit from transaction (atomic batch insert, can rollback)
- No wasted BEGIN/;/ROLLBACK cycles before upserts
- Clean traces: dimension upserts show as individual commits, facts in one transaction

Example trace pattern:
- BEFORE: BEGIN → ; → ROLLBACK → many SELECTs → upserts → INSERT facts → COMMIT (5+ seconds)
- AFTER: upsert → commit, upsert → commit, BEGIN → INSERT facts → COMMIT (<200ms)
"""

import hashlib
import json
import logging
import os
import time
from base64 import b64decode
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from opentelemetry import context as context_api
from opentelemetry import trace
from sqlalchemy import case, cast, create_engine, distinct, func, or_, select, text
from sqlalchemy.dialects.postgresql import INTEGER, insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.api import (
    LogRecord,
    Metric,
    Service,
    ServiceMapEdge,
    ServiceMapNode,
    Span,
    SpanAttribute,
    SpanEvent,
    SpanLink,
)
from app.models.database import (
    LogsFact,
    MetricsFact,
    NamespaceDim,
    OperationDim,
    ResourceDim,
    ServiceDim,
    SpansFact,
    TenantDim,
)
from common import metrics as storage_metrics

logger = logging.getLogger(__name__)


def _timestamp_to_rfc3339(ts: datetime, nanos_fraction: int = 0) -> str:
    """Convert Python datetime + nanosecond fraction to RFC3339 timestamp string.

    Args:
        ts: Python datetime object (microsecond precision from PostgreSQL TIMESTAMPTZ)
        nanos_fraction: Additional nanoseconds (0-999) beyond microsecond precision

    Returns:
        RFC3339 formatted timestamp string with nanosecond precision
        Example: "2026-01-25T17:30:45.123456789Z"
    """
    # Get microseconds from datetime (PostgreSQL TIMESTAMPTZ has microsecond precision)
    micros = ts.microsecond
    # Convert to nanoseconds and add the additional nanos_fraction
    nanos = micros * 1000 + nanos_fraction
    # Format with full nanosecond precision
    return f"{ts.strftime('%Y-%m-%dT%H:%M:%S')}.{nanos:09d}Z"


def _rfc3339_to_timestamp_nanos(rfc: str) -> tuple[datetime, int]:
    """Convert RFC3339 timestamp string to Python datetime + nanosecond fraction.

    Args:
        rfc: RFC3339 formatted timestamp string
        Examples: "2026-01-25T17:30:45.123456789Z", "2026-01-25T17:30:45Z"

    Returns:
        Tuple of (datetime with microsecond precision, nanos_fraction 0-999)
    """
    # Remove 'Z' suffix if present
    rfc = rfc.rstrip("Z")

    # Split seconds and fractional part
    if "." in rfc:
        base, frac = rfc.rsplit(".", 1)
        # Pad or truncate to 9 digits (nanoseconds)
        frac = frac.ljust(9, "0")[:9]
        # Split into microseconds (first 6 digits) and nanos_fraction (last 3 digits)
        micros = int(frac[:6])
        nanos_fraction = int(frac[6:9])
    else:
        base = rfc
        micros = 0
        nanos_fraction = 0

    # Parse datetime with microsecond precision
    dt = datetime.fromisoformat(base)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC, microsecond=micros)
    else:
        dt = dt.replace(microsecond=micros)

    return dt, nanos_fraction


def _nanoseconds_to_timestamp_nanos(ns: int) -> tuple[datetime, int]:
    """Convert nanoseconds since Unix epoch to Python datetime + nanosecond fraction.

    Used for converting OTLP nanosecond timestamps to PostgreSQL TIMESTAMPTZ + nanos_fraction.

    Args:
        ns: Nanoseconds since Unix epoch (1970-01-01T00:00:00Z)

    Returns:
        Tuple of (datetime with microsecond precision, nanos_fraction 0-999)
    """
    # Split nanoseconds into seconds, microseconds, and nanos_fraction
    seconds = ns // 1_000_000_000
    remainder_nanos = ns % 1_000_000_000
    micros = remainder_nanos // 1000
    nanos_fraction = remainder_nanos % 1000

    # Create datetime with microsecond precision
    dt = datetime.fromtimestamp(seconds, tz=UTC)
    dt = dt.replace(microsecond=micros)

    return dt, nanos_fraction


def _timestamp_nanos_to_nanoseconds(ts: datetime, nanos_fraction: int = 0) -> int:
    """Convert Python datetime + nanosecond fraction to nanoseconds since Unix epoch.

    Used for API time range queries (which still use nanosecond integers).

    Args:
        ts: Python datetime object
        nanos_fraction: Additional nanoseconds (0-999)

    Returns:
        Nanoseconds since Unix epoch (1970-01-01T00:00:00Z)
    """
    seconds = int(ts.timestamp())
    micros = ts.microsecond
    return seconds * 1_000_000_000 + micros * 1000 + nanos_fraction


def _calculate_duration_seconds(start_ts: datetime, start_nanos: int, end_ts: datetime, end_nanos: int) -> float:
    """Calculate duration in seconds from timestamp + nanos_fraction pairs.

    Args:
        start_ts: Start datetime
        start_nanos: Start nanosecond fraction (0-999)
        end_ts: End datetime
        end_nanos: End nanosecond fraction (0-999)

    Returns:
        Duration in seconds with fractional precision
        Example: 1.234567890 (1 second and 234567890 nanoseconds)
    """
    start_ns = _timestamp_nanos_to_nanoseconds(start_ts, start_nanos)
    end_ns = _timestamp_nanos_to_nanoseconds(end_ts, end_nanos)
    return (end_ns - start_ns) / 1_000_000_000


class PostgresStorage:
    """PostgreSQL storage backend using SQLModel ORM with cross-batch dimension caching."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine: Engine | None = None  # For fact inserts with explicit transactions
        self.autocommit_engine: Engine | None = None  # For dimension upserts with autocommit

        # Cross-batch dimension cache (GIL-protected dict operations)
        self._dimension_cache: dict[tuple, tuple[int, datetime]] = {}  # cache_key -> (dim_id, last_upserted)
        self._cache_ttl_seconds = int(os.getenv("DIMENSION_CACHE_TTL_SECONDS", "1800"))  # 30 minutes default
        self._cache_ttl = timedelta(seconds=self._cache_ttl_seconds)

        # Minimum time between last_seen updates (default 5 minutes)
        self._last_seen_update_interval = timedelta(seconds=int(os.getenv("LAST_SEEN_UPDATE_INTERVAL_SECONDS", "300")))

        # Cache observability (via OTel span events only)
        self._cache_hits = 0
        self._cache_misses = 0

    def connect(self) -> None:
        """Initialize database engines (normal + autocommit)."""
        # Normal engine for fact inserts with explicit transactions
        self.engine = create_engine(
            self.connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        # Autocommit engine for dimension upserts (idempotent, multi-process safe)
        self.autocommit_engine = create_engine(
            self.connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )

        # Register partition health metrics callback
        storage_metrics.register_partition_health_callbacks(self._get_partition_health_stats)

    def _get_partition_health_stats(self) -> dict[str, Any]:
        """Get partition health statistics for metrics callback.

        Returns:
            Dictionary with partition_count, total_size_bytes, oldest_partition_age_days
        """
        try:
            if not self.engine:
                return {"partition_count": 0, "total_size_bytes": 0, "oldest_partition_age_days": 0}

            with Session(self.engine) as session:
                # Query partition information from pg_inherits and pg_class
                # This gets child tables (partitions) of spans_fact, logs_fact, metrics_fact
                # Note: relcreated doesn't exist in PostgreSQL, using pg_stat_user_tables instead
                query = """
                SELECT
                    COUNT(DISTINCT c.oid) as partition_count,
                    COALESCE(SUM(pg_total_relation_size(c.oid)), 0) as total_size_bytes,
                    0 as oldest_partition_age_days
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'r'
                    AND c.relispartition = true
                    AND n.nspname = 'public'
                    AND c.relname LIKE '%_fact_%';
                """
                result = session.execute(text(query))
                row = result.fetchone()
                if row:
                    return {
                        "partition_count": int(row[0]),
                        "total_size_bytes": int(row[1]),
                        "oldest_partition_age_days": float(row[2]),
                    }
                return {"partition_count": 0, "total_size_bytes": 0, "oldest_partition_age_days": 0}
        except Exception as e:
            logging.error(f"Error getting partition health stats: {e}")
            return {"partition_count": 0, "total_size_bytes": 0, "oldest_partition_age_days": 0}

    def get_connection_pool_stats(self) -> dict[str, int]:
        """Get connection pool statistics for observability.

        Returns:
            Dictionary with pool_size, checked_out, checked_in, overflow, overflow_in_use
        """
        stats = {
            "pool_size": 0,
            "checked_out": 0,
            "checked_in": 0,
            "overflow": 0,
            "overflow_in_use": 0,
        }

        if self.engine:
            pool = self.engine.pool
            stats["pool_size"] = pool.size()
            stats["checked_out"] = pool.checkedout()
            stats["checked_in"] = pool.size() - pool.checkedout()
            stats["overflow"] = pool.overflow()
            stats["overflow_in_use"] = pool.overflow() if pool.overflow() > 0 else 0

            # Record metrics
            storage_metrics.record_connection_pool_state(
                active=stats["checked_out"],
                idle=stats["checked_in"],
                waiting=0,  # psycopg2 doesn't expose waiting threads
            )

        return stats

    def close(self) -> None:
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
        if self.autocommit_engine:
            self.autocommit_engine.dispose()

    def _check_cache(self, cache_key: tuple) -> int | None:
        """Check if dimension is cached and not expired.

        Returns:
            dimension_id if cache hit, None if miss or expired
        """
        now = datetime.now(UTC)

        # Dict operations are atomic in Python (GIL-protected)
        if cache_key in self._dimension_cache:
            dim_id, last_upserted = self._dimension_cache[cache_key]
            age = now - last_upserted

            if age < self._cache_ttl:
                # Cache hit
                self._cache_hits += 1
                # Record cache hit metric (dimension_type from cache_key[0])
                dimension_type = cache_key[0] if isinstance(cache_key, tuple) else "unknown"
                storage_metrics.record_dimension_cache_operation(
                    dimension_type=dimension_type,
                    hit=True,
                )
                return dim_id

            # Cache expired - will be refreshed by upsert
            self._cache_misses += 1
            # Record cache miss metric
            dimension_type = cache_key[0] if isinstance(cache_key, tuple) else "unknown"
            storage_metrics.record_dimension_cache_operation(
                dimension_type=dimension_type,
                hit=False,
                attributes={"reason": "expired"},
            )
            return None

        # Cache miss
        self._cache_misses += 1
        # Record cache miss metric
        dimension_type = cache_key[0] if isinstance(cache_key, tuple) else "unknown"
        storage_metrics.record_dimension_cache_operation(
            dimension_type=dimension_type,
            hit=False,
            attributes={"reason": "not_found"},
        )
        return None

    def _update_cache(self, cache_key: tuple, dim_id: int) -> None:
        """Update cache with dimension ID and current timestamp."""
        now = datetime.now(UTC)
        # Dict assignment is atomic in Python (GIL-protected)
        self._dimension_cache[cache_key] = (dim_id, now)

    def health_check(self) -> dict[str, Any]:
        """Check database connectivity."""
        if not self.engine:
            return {"status": "not_connected", "message": "Engine not initialized"}

        try:
            with Session(self.engine) as session:
                # Use ORM select instead of text()
                result = session.execute(select(func.count()).select_from(SpansFact).limit(1))
                result.scalar()
            return {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "message": str(e)}

    @staticmethod
    def _base64_to_hex(b64_str: str) -> str:
        """Convert base64 trace/span ID to hex.

        If input is already hex (all hex digits), return as-is.
        Otherwise, decode from base64 to bytes, then to hex.
        """
        if not b64_str:
            return b64_str

        # Check if already hex (all chars are 0-9a-fA-F)
        if all(c in "0123456789abcdefABCDEF" for c in b64_str):
            return b64_str.lower()

        # Otherwise decode from base64
        try:
            return b64decode(b64_str).hex()
        except Exception:
            return b64_str  # Invalid format, return as-is

    @staticmethod
    def _bytes_to_hex(value: bytes | str | None) -> str | None:
        """Convert bytes to hex string, or pass through if already string."""
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.hex()
        return value

    @staticmethod
    def _normalize_span_kind(kind: int | str | None) -> int:
        """Convert span kind to integer."""
        if isinstance(kind, int):
            return kind
        if isinstance(kind, str):
            kind_map = {
                "SPAN_KIND_UNSPECIFIED": 0,
                "SPAN_KIND_INTERNAL": 1,
                "SPAN_KIND_SERVER": 2,
                "SPAN_KIND_CLIENT": 3,
                "SPAN_KIND_PRODUCER": 4,
                "SPAN_KIND_CONSUMER": 5,
            }
            return kind_map.get(kind, 0)
        return 0

    @staticmethod
    def _normalize_status_code(code: int | str | None) -> int | None:
        """Convert status code to integer."""
        if code is None:
            return None
        if isinstance(code, int):
            return code
        if isinstance(code, str):
            code_map = {
                "STATUS_CODE_UNSET": 0,
                "STATUS_CODE_OK": 1,
                "STATUS_CODE_ERROR": 2,
            }
            return code_map.get(code, 0)
        return 0

    @staticmethod
    def _normalize_severity_number(severity: int | str | None) -> int | None:
        """Convert severity number to integer."""
        if severity is None:
            return None
        if isinstance(severity, int):
            return severity
        if isinstance(severity, str):
            severity_map = {
                "SEVERITY_NUMBER_UNSPECIFIED": 0,
                "SEVERITY_NUMBER_TRACE": 1,
                "SEVERITY_NUMBER_DEBUG": 5,
                "SEVERITY_NUMBER_INFO": 9,
                "SEVERITY_NUMBER_WARN": 13,
                "SEVERITY_NUMBER_ERROR": 17,
                "SEVERITY_NUMBER_FATAL": 21,
            }
            return severity_map.get(severity, 0)
        return 0

    @staticmethod
    def _extract_string_value(attr_value: dict) -> str | None:
        """Extract string from OTLP attribute value."""
        if "string_value" in attr_value:
            return attr_value["string_value"]
        if "int_value" in attr_value:
            return attr_value["int_value"]
        if "double_value" in attr_value:
            return attr_value["double_value"]
        if "bool_value" in attr_value:
            return attr_value["bool_value"]
        return None

    @staticmethod
    def _apply_namespace_filtering(stmt: Any, filters: list | None) -> tuple[Any, list]:
        """Apply namespace filtering with proper JOIN strategy and OR logic.

        Returns:
            tuple: (modified statement, list of namespace filters)
        """

        # Extract namespace filters
        namespace_filters = []
        if filters:
            namespace_filters = [f for f in filters if f.field == "service_namespace"]

        # Determine if we need INNER or OUTER join to NamespaceDim
        # Use INNER join if filtering for any non-empty namespace, else OUTER join
        use_inner_join = any(f.value != "" for f in namespace_filters)

        if use_inner_join:
            stmt = stmt.join(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
        else:
            stmt = stmt.outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)

        # Apply namespace filters with OR logic
        if namespace_filters:
            namespace_conditions = []
            for f in namespace_filters:
                if f.value == "":
                    namespace_conditions.append(ServiceDim.namespace_id.is_(None))
                else:
                    namespace_conditions.append(NamespaceDim.namespace == f.value)

            if namespace_conditions:
                stmt = stmt.where(or_(*namespace_conditions))

        return stmt, namespace_filters

    @staticmethod
    def _apply_traceid_filter(fact_model: Any, stmt: Any, filters: list | None) -> tuple[Any, list]:
        """Apply trace_id filtering with support for NULL values (valid for logs).

        Args:
            fact_model: The fact table model class (LogsFact, SpansFact, etc.)
            stmt: SQLAlchemy select statement
            filters: List of Filter objects

        Returns:
            tuple: (modified statement, list of traceid filters)
        """

        # Extract trace_id filters
        traceid_filters = []
        if filters:
            traceid_filters = [f for f in filters if f.field == "trace_id"]

        # Apply trace_id filters with OR logic
        if traceid_filters:
            traceid_conditions = []
            for f in traceid_filters:
                if f.value == "" or f.value is None or f.value.lower() == "null":
                    # NULL trace_id is valid for logs (not correlated with traces)
                    traceid_conditions.append(fact_model.trace_id.is_(None))
                else:
                    traceid_conditions.append(fact_model.trace_id == f.value)

            if traceid_conditions:
                stmt = stmt.where(or_(*traceid_conditions))

        return stmt, traceid_filters

    @staticmethod
    def _apply_spanid_filter(fact_model: Any, stmt: Any, filters: list | None) -> tuple[Any, list]:
        """Apply span_id filtering. NULL span_id is never valid, always filter by value.

        Args:
            fact_model: The fact table model class (LogsFact, SpansFact, etc.)
            stmt: SQLAlchemy select statement
            filters: List of Filter objects

        Returns:
            tuple: (modified statement, list of spanid filters)
        """

        # Extract span_id filters (never allow NULL)
        spanid_filters = []
        if filters:
            spanid_filters = [f for f in filters if f.field == "span_id" and f.value and f.value.lower() != "null"]

        # Apply span_id filters with OR logic
        if spanid_filters:
            spanid_conditions = [fact_model.span_id == f.value for f in spanid_filters]
            if spanid_conditions:
                stmt = stmt.where(or_(*spanid_conditions))

        return stmt, spanid_filters

    @staticmethod
    def _apply_log_level_filter(stmt: Any, filters: list | None) -> tuple[Any, list]:
        """Apply log level filtering using OTel severity_number ranges.

        OTel Severity Mapping:
        - TRACE: 1-4
        - DEBUG: 5-8
        - INFO: 9-12
        - WARN: 13-16
        - ERROR: 17-20
        - FATAL: 21-24

        Args:
            stmt: SQLAlchemy select statement
            filters: List of Filter objects

        Returns:
            tuple: (modified statement, list of log_level filters)
        """

        # Define severity_number ranges per OTel spec
        SEVERITY_RANGES = {
            "TRACE": (1, 4),
            "DEBUG": (5, 8),
            "INFO": (9, 12),
            "WARN": (13, 16),
            "ERROR": (17, 20),
            "FATAL": (21, 24),
        }

        # Extract log_level filters
        log_level_filters = []
        if filters:
            log_level_filters = [f for f in filters if f.field == "log_level"]

        # Apply log level filters with OR logic using severity_number ranges
        if log_level_filters:
            level_conditions = []
            for f in log_level_filters:
                level_upper = f.value.upper()
                if level_upper in SEVERITY_RANGES:
                    min_sev, max_sev = SEVERITY_RANGES[level_upper]
                    level_conditions.append(LogsFact.severity_number.between(min_sev, max_sev))

            if level_conditions:
                stmt = stmt.where(or_(*level_conditions))

        return stmt, log_level_filters

    @staticmethod
    def _apply_http_status_filter(stmt: Any, filters: list | None) -> tuple[Any, list]:
        """Apply HTTP status code filtering using ranges (2xx, 4xx, 5xx) or unknown (NULL).

        Status code is extracted from span attributes (http.status_code).

        Args:
            stmt: SQLAlchemy select statement
            filters: List of Filter objects

        Returns:
            tuple: (modified statement, list of http_status filters)
        """

        # Extract http_status filters
        http_status_filters = []
        if filters:
            http_status_filters = [f for f in filters if f.field == "http_status"]

        # Apply HTTP status filters with OR logic
        if http_status_filters:
            status_conditions = []
            for f in http_status_filters:
                value = f.value.lower()
                if value == "2xx":
                    # Match 200-299 in attributes->'http.status_code'
                    status_conditions.append(
                        cast(SpansFact.attributes["http.status_code"].as_string(), INTEGER).between(200, 299)
                    )
                elif value == "4xx":
                    # Match 400-499
                    status_conditions.append(
                        cast(SpansFact.attributes["http.status_code"].as_string(), INTEGER).between(400, 499)
                    )
                elif value == "5xx":
                    # Match 500-599
                    status_conditions.append(
                        cast(SpansFact.attributes["http.status_code"].as_string(), INTEGER).between(500, 599)
                    )
                elif value == "unknown":
                    # Match NULL or missing http.status_code
                    status_conditions.append(
                        or_(
                            SpansFact.attributes["http.status_code"].is_(None),
                            ~SpansFact.attributes.has_key("http.status_code"),
                        )
                    )

            if status_conditions:
                stmt = stmt.where(or_(*status_conditions))

        return stmt, http_status_filters

    def _get_unknown_tenant_id(self) -> int:
        """Get/create 'unknown' tenant (has unique constraint on name)."""

        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(TenantDim)
                .values(name="unknown")
                .on_conflict_do_nothing(index_elements=["name"])
                .returning(TenantDim.id)
            )
            result = session.execute(stmt)
            tenant_id = result.scalar()
            if tenant_id is None:
                # Already exists, fetch it
                stmt = select(TenantDim.id).where(TenantDim.name == "unknown")
                result = session.execute(stmt)
                tenant_id = result.scalar()
            return tenant_id

    def _get_unknown_connection_id(self) -> int:
        """Return seeded 'unknown' connection ID (always 1)."""
        return 1

    def _upsert_namespace(self, tenant_id: int, namespace: str | None = None) -> int:
        """Upsert namespace with autocommit - idempotent, multi-process safe.

        Only updates last_seen if:
        1. This is a new namespace (INSERT), OR
        2. last_seen is older than LAST_SEEN_UPDATE_INTERVAL_SECONDS (default 5 minutes)

        Uses GREATEST() to ensure last_seen never regresses (other processes may update concurrently).

        Note: Allows NULL namespace - constraint UNIQUE NULLS NOT DISTINCT ensures single NULL per tenant.
        """
        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(NamespaceDim)
                .values(tenant_id=tenant_id, namespace=namespace, first_seen=now, last_seen=now)
                .on_conflict_do_update(
                    index_elements=["tenant_id", "namespace"],
                    # Only update if last_seen is stale (older than threshold)
                    # Use GREATEST() to ensure we never set an older timestamp
                    set_={
                        "last_seen": case(
                            (NamespaceDim.last_seen < min_last_seen, now),
                            else_=NamespaceDim.last_seen,
                        )
                    },
                )
                .returning(NamespaceDim.id)
            )
            result = session.execute(stmt)
            namespace_id = result.scalar_one()  # Will raise if no rows returned

            # Only set span attributes if we have valid span and non-None values
            span = trace.get_current_span()
            if span.is_recording():
                span.set_attribute("db.namespace", namespace or "NULL")
                span.set_attribute("db.namespace_id", namespace_id)
            return namespace_id

    def _upsert_service(self, tenant_id: int, name: str, namespace: str | None = None) -> int:
        """Upsert service with autocommit - idempotent, multi-process safe.

        Only updates last_seen if it's older than LAST_SEEN_UPDATE_INTERVAL_SECONDS.
        Uses GREATEST() to prevent time regression from concurrent updates.
        """
        # First upsert namespace (autocommit - immediately visible to all processes)
        namespace_id = self._upsert_namespace(tenant_id, namespace)

        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(ServiceDim)
                .values(tenant_id=tenant_id, name=name, namespace_id=namespace_id, first_seen=now, last_seen=now)
                .on_conflict_do_update(
                    index_elements=["name", "namespace_id"],
                    set_={
                        "last_seen": case(
                            (ServiceDim.last_seen < min_last_seen, now),
                            else_=ServiceDim.last_seen,
                        )
                    },
                )
                .returning(ServiceDim.id)
            )
            result = session.execute(stmt)
            service_id = result.scalar_one()  # Will raise if no rows returned

            # Only set span attributes if we have valid span
            span = trace.get_current_span()
            if span.is_recording():
                span.set_attribute("db.service_name", name)
                span.set_attribute("db.service_id", service_id)
                span.set_attribute("db.namespace_id", namespace_id)
            return service_id

    def _upsert_operation(self, tenant_id: int, service_id: int, name: str, span_kind: int | None = None) -> int:
        """Upsert operation with autocommit - idempotent, multi-process safe.

        Only updates last_seen if it's older than LAST_SEEN_UPDATE_INTERVAL_SECONDS.
        Uses GREATEST() to prevent time regression from concurrent updates.
        """
        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(OperationDim)
                .values(
                    tenant_id=tenant_id,
                    service_id=service_id,
                    name=name,
                    span_kind=span_kind,
                    first_seen=now,
                    last_seen=now,
                )
                .on_conflict_do_update(
                    index_elements=["tenant_id", "service_id", "name", "span_kind"],
                    set_={
                        "last_seen": case(
                            (OperationDim.last_seen < min_last_seen, now),
                            else_=OperationDim.last_seen,
                        )
                    },
                )
                .returning(OperationDim.id)
            )
            result = session.execute(stmt)
            operation_id = result.scalar_one()  # Will raise if no rows returned

            return operation_id

    def _upsert_resource(self, tenant_id: int, attributes: dict) -> int:
        """Upsert resource with autocommit - idempotent, multi-process safe.

        Only updates last_seen if it's older than LAST_SEEN_UPDATE_INTERVAL_SECONDS.
        Uses GREATEST() to prevent time regression from concurrent updates.
        """
        resource_json = json.dumps(attributes, sort_keys=True)
        resource_hash = hashlib.sha256(resource_json.encode()).hexdigest()

        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(ResourceDim)
                .values(
                    tenant_id=tenant_id,
                    resource_hash=resource_hash,
                    attributes=attributes,
                    first_seen=now,
                    last_seen=now,
                )
                .on_conflict_do_update(
                    index_elements=["tenant_id", "resource_hash"],
                    set_={
                        "last_seen": case(
                            (ResourceDim.last_seen < min_last_seen, now),
                            else_=ResourceDim.last_seen,
                        )
                    },
                )
                .returning(ResourceDim.id)
            )
            result = session.execute(stmt)
            resource_id = result.scalar_one()  # Will raise if no rows returned

            return resource_id

    def _process_resource_dimensions(
        self,
        resources: list[dict],
        signal_type: str,
        main_span: trace.Span,
    ) -> tuple[int, int, dict[tuple[str, str | None], int]]:
        """Process resource dimensions in a separate linked trace.

        Creates a new trace linked to the main trace for dimension operations.
        Ensures tenant/connection retrieval happens inside dimension span.

        Args:
            resources: List of OTLP resource dicts with attributes
            signal_type: "traces", "logs", or "metrics" for span naming
            main_span: The main span from the calling method

        Returns:
            Tuple of (tenant_id, connection_id, service_map)
            where service_map is {(service_name, namespace): service_id}
        """
        # Extract unique services from resources
        unique_services = {}  # (service_name, namespace) -> service_id

        for resource in resources:
            resource_attrs = resource.get("attributes", [])

            service_name = "unknown"
            service_namespace = None
            for attr in resource_attrs:
                key = attr.get("key")
                value = attr.get("value", {})
                if key == "service.name":
                    service_name = self._extract_string_value(value) or "unknown"
                elif key == "service.namespace":
                    service_namespace = self._extract_string_value(value)

            service_key = (service_name, service_namespace)
            if service_key not in unique_services:
                unique_services[service_key] = None  # Will be populated later

        # Create separate linked trace for dimension operations
        tracer = trace.get_tracer(__name__)
        main_span_context = main_span.get_span_context()
        span_link = trace.Link(main_span_context)

        # Create detached context (new trace)
        new_context = context_api.Context()

        # Start span in detached context (new trace)
        dim_span = tracer.start_span(
            f"upsert_dimensions_{signal_type}",
            context=new_context,
            kind=trace.SpanKind.INTERNAL,
            links=[span_link],
            attributes={
                "db.operation": "upsert_dimensions",
                "db.signal_type": signal_type,
                "db.unique_services": len(unique_services),
            },
        )

        # CRITICAL: Use trace.use_span() to activate dimension span
        # SQLAlchemy instrumentation creates child spans in this trace
        with trace.use_span(dim_span, end_on_exit=True):
            # Get tenant/connection INSIDE dimension span (their DB ops tracked here)
            tenant_id = self._get_unknown_tenant_id()
            connection_id = self._get_unknown_connection_id()

            # Upsert services
            for service_key in unique_services:
                service_name, service_namespace = service_key
                cache_key = ("service", tenant_id, service_name, service_namespace)

                cached_id = self._check_cache(cache_key)
                if cached_id is not None:
                    service_id = cached_id
                else:
                    service_id = self._upsert_service(tenant_id, service_name, service_namespace)
                    self._update_cache(cache_key, service_id)

                unique_services[service_key] = service_id

            dim_span.set_attribute("db.dimensions.services_upserted", len(unique_services))

        # Add event to main span (for visibility)
        main_span.add_event(
            "dimensions_upserted",
            {
                "signal_type": signal_type,
                "services": len(unique_services),
            },
        )

        return tenant_id, connection_id, unique_services

    def store_traces(self, resource_spans: list[dict]) -> int:
        """Store OTLP traces using autocommit for dimensions, explicit transaction for facts.

        Transaction strategy:
        1. Cache tenant_id and connection_id (one SELECT each, reused for all spans)
        2. Dimension upserts with autocommit (namespace, service, operation, resource)
           - Each upsert commits immediately - idempotent, multi-process safe
        3. Fact inserts in explicit transaction after dimensions committed
           - All span rows in single transaction (atomic, can rollback)

        OTLP structure (with preserving_proto_field_name=True):
        resource_spans: []
          ├─ resource: { attributes: [] }
          └─ scope_spans: []  # snake_case
              ├─ scope: {}
              └─ spans: []
        """
        if not resource_spans:
            return 0

        otel_span = trace.get_current_span()
        otel_span.set_attribute("db.batch.resource_spans", len(resource_spans))

        # Extract resources for common dimension processing
        resources = [rs.get("resource", {}) for rs in resource_spans]

        # Process common dimensions (tenant, connection, service) in separate linked trace
        tenant_id, connection_id, unique_services = self._process_resource_dimensions(
            resources=resources,
            signal_type="traces",
            main_span=otel_span,
        )

        # TRACE-SPECIFIC: Collect unique resources and operations
        unique_resources = {}  # resource_hash -> (resource_dict, resource_id)
        unique_operations = {}  # (service_key, operation_name, span_kind) -> None

        for resource_span in resource_spans:
            resource = resource_span.get("resource", {})
            resource_attrs = resource.get("attributes", [])
            resource_dict = {attr["key"]: attr.get("value") for attr in resource_attrs}

            # Extract service key for operation mapping
            service_name = "unknown"
            service_namespace = None
            for attr in resource_attrs:
                key = attr.get("key")
                value = attr.get("value", {})
                if key == "service.name":
                    service_name = self._extract_string_value(value) or "unknown"
                elif key == "service.namespace":
                    service_namespace = self._extract_string_value(value)
            service_key = (service_name, service_namespace)

            # Track unique resource
            resource_json = json.dumps(resource_dict, sort_keys=True)
            resource_hash = hashlib.sha256(resource_json.encode()).hexdigest()
            if resource_hash not in unique_resources:
                unique_resources[resource_hash] = (resource_dict, None)

            # Track unique operations
            for scope_span in resource_span.get("scope_spans", []):
                for span in scope_span.get("spans", []):
                    name = span.get("name", "unknown")
                    kind_raw = span.get("kind", 0)
                    kind = self._normalize_span_kind(kind_raw)
                    op_key = (service_key, name, kind)
                    if op_key not in unique_operations:
                        unique_operations[op_key] = None

        # Upsert trace-specific dimensions (resources, operations) in separate linked trace
        tracer = trace.get_tracer(__name__)
        main_span_context = otel_span.get_span_context()
        span_link = trace.Link(main_span_context)
        new_context = context_api.Context()

        dim_span = tracer.start_span(
            "upsert_trace_dimensions",
            context=new_context,
            kind=trace.SpanKind.INTERNAL,
            links=[span_link],
            attributes={
                "db.operation": "upsert_trace_dimensions",
                "db.unique_resources": len(unique_resources),
                "db.unique_operations": len(unique_operations),
            },
        )

        with trace.use_span(dim_span, end_on_exit=True):
            # Upsert resources
            for resource_hash, (resource_dict, _) in unique_resources.items():
                cache_key = ("resource", tenant_id, resource_hash)
                cached_id = self._check_cache(cache_key)
                if cached_id is not None:
                    resource_id = cached_id
                else:
                    resource_id = self._upsert_resource(tenant_id, resource_dict)
                    self._update_cache(cache_key, resource_id)
                unique_resources[resource_hash] = (resource_dict, resource_id)

            # Upsert operations (needs service_ids from unique_services)
            operations_by_service_and_op = {}
            for op_key in unique_operations:
                service_key, name, kind = op_key
                service_id = unique_services[service_key]
                real_op_key = (service_id, name, kind)
                if real_op_key not in operations_by_service_and_op:
                    cache_key = ("operation", tenant_id, service_id, name, kind)
                    cached_id = self._check_cache(cache_key)
                    if cached_id is not None:
                        operation_id = cached_id
                    else:
                        operation_id = self._upsert_operation(tenant_id, service_id, name, kind)
                        self._update_cache(cache_key, operation_id)
                    operations_by_service_and_op[real_op_key] = operation_id

            dim_span.set_attribute("db.dimensions.resources_upserted", len(unique_resources))
            dim_span.set_attribute("db.dimensions.operations_upserted", len(operations_by_service_and_op))

        otel_span.add_event(
            "trace_dimensions_upserted",
            {
                "resources": len(unique_resources),
                "operations": len(operations_by_service_and_op),
            },
        )

        # Build spans using cached dimension IDs
        spans_to_insert = []
        for resource_span in resource_spans:
            resource = resource_span.get("resource", {})
            resource_attrs = resource.get("attributes", [])
            resource_dict = {attr["key"]: attr.get("value") for attr in resource_attrs}

            service_name = "unknown"
            service_namespace = None
            for attr in resource_attrs:
                key = attr.get("key")
                value = attr.get("value", {})
                if key == "service.name":
                    service_name = self._extract_string_value(value) or "unknown"
                elif key == "service.namespace":
                    service_namespace = self._extract_string_value(value)

            # Lookup cached IDs (no DB calls)
            service_key = (service_name, service_namespace)
            service_id = unique_services[service_key]

            resource_json = json.dumps(resource_dict, sort_keys=True)
            resource_hash = hashlib.sha256(resource_json.encode()).hexdigest()
            _, resource_id = unique_resources[resource_hash]

            # Use snake_case (preserving_proto_field_name=True)
            for scope_span in resource_span.get("scope_spans", []):
                scope = scope_span.get("scope", {})

                for span in scope_span.get("spans", []):
                    # IDs - convert base64 to hex
                    trace_id_raw = span.get("trace_id", "")
                    span_id_raw = span.get("span_id", "")

                    # OTLP spec: trace_id is 16 bytes (32 hex), span_id is 8 bytes (16 hex)
                    # If already hex (32 or 16 chars), use as-is. If base64, convert.
                    if len(trace_id_raw) == 32:
                        trace_id = trace_id_raw
                    else:
                        trace_id = self._base64_to_hex(trace_id_raw) if trace_id_raw else ""

                    if len(span_id_raw) == 16:
                        span_id = span_id_raw
                    else:
                        span_id = self._base64_to_hex(span_id_raw) if span_id_raw else ""

                    parent_span_id_raw = span.get("parent_span_id")
                    if parent_span_id_raw:
                        if len(parent_span_id_raw) == 16:
                            parent_span_id = parent_span_id_raw
                        else:
                            parent_span_id = self._base64_to_hex(parent_span_id_raw)
                    else:
                        parent_span_id = None

                    name = span.get("name", "unknown")
                    kind_raw = span.get("kind", 0)
                    kind = self._normalize_span_kind(kind_raw)

                    # Timestamps - use snake_case
                    start_time_raw = span.get("start_time_unix_nano", "0")
                    end_time_raw = span.get("end_time_unix_nano", "0")
                    start_time_ns = int(start_time_raw) if start_time_raw else 0
                    end_time_ns = int(end_time_raw) if end_time_raw else 0

                    # Convert nanoseconds to timestamp + nanos_fraction
                    start_timestamp, start_nanos_fraction = _nanoseconds_to_timestamp_nanos(start_time_ns)
                    end_timestamp, end_nanos_fraction = _nanoseconds_to_timestamp_nanos(end_time_ns)

                    # Lookup cached operation_id (no DB call)
                    real_op_key = (service_id, name, kind)
                    operation_id = operations_by_service_and_op[real_op_key]

                    status = span.get("status", {})
                    status_code = self._normalize_status_code(status.get("code"))
                    status_message = status.get("message")

                    attrs_list = span.get("attributes", [])
                    attributes = {attr["key"]: attr.get("value") for attr in attrs_list}

                    # Convert link trace_id/span_id from base64 to hex for consistency
                    links_raw = span.get("links", [])
                    links_normalized = []
                    for link in links_raw:
                        link_trace_id_raw = link.get("trace_id", "") or link.get("traceId", "")
                        link_span_id_raw = link.get("span_id", "") or link.get("spanId", "")

                        # Convert to hex if base64
                        if link_trace_id_raw:
                            if len(link_trace_id_raw) == 32:
                                link_trace_id = link_trace_id_raw  # Already hex
                            else:
                                link_trace_id = self._base64_to_hex(link_trace_id_raw)
                        else:
                            link_trace_id = ""

                        if link_span_id_raw:
                            if len(link_span_id_raw) == 16:
                                link_span_id = link_span_id_raw  # Already hex
                            else:
                                link_span_id = self._base64_to_hex(link_span_id_raw)
                        else:
                            link_span_id = ""

                        # Store normalized link
                        normalized_link = {
                            "trace_id": link_trace_id,
                            "span_id": link_span_id,
                            "attributes": link.get("attributes", []),
                            "trace_state": link.get("trace_state", "") or link.get("traceState", ""),
                            "dropped_attributes_count": link.get("dropped_attributes_count", 0),
                        }
                        links_normalized.append(normalized_link)

                    span_obj = SpansFact(
                        tenant_id=tenant_id,
                        connection_id=connection_id,
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        name=name,
                        kind=kind,
                        status_code=status_code,
                        status_message=status_message,
                        start_timestamp=start_timestamp,
                        start_nanos_fraction=start_nanos_fraction,
                        end_timestamp=end_timestamp,
                        end_nanos_fraction=end_nanos_fraction,
                        service_id=service_id,
                        operation_id=operation_id,
                        resource_id=resource_id,
                        attributes=attributes,
                        events=span.get("events", []),
                        links=links_normalized,
                        resource=resource_dict,
                        scope=scope,
                        flags=span.get("flags", 0),
                        dropped_attributes_count=span.get("dropped_attributes_count", 0),
                        dropped_events_count=span.get("dropped_events_count", 0),
                        dropped_links_count=span.get("dropped_links_count", 0),
                    )
                    spans_to_insert.append(span_obj)

        # Insert all facts in explicit transaction (after dimensions committed)
        if spans_to_insert:
            # Manual span for bulk insert performance tracking
            try:
                with (
                    tracer.start_as_current_span(
                        "db.bulk_insert_spans",
                        kind=trace.SpanKind.INTERNAL,
                        attributes={
                            "db.operation": "INSERT",
                            "db.system": "postgresql",
                            "db.table": "spans_fact",
                            "db.batch_size": len(spans_to_insert),
                        },
                    ),
                    Session(self.engine) as session,
                    session.begin(),
                ):  # Explicit transaction
                    session.add_all(spans_to_insert)
                    # Transaction commits at end of block
                otel_span.add_event("spans_inserted", {"count": len(spans_to_insert)})

                # Record ingestion metrics
                storage_metrics.record_spans_ingested(
                    count=len(spans_to_insert),
                    attributes={"tenant_id": tenant_id},
                )
                storage_metrics.record_ingestion_batch_size(
                    size=len(spans_to_insert),
                    signal_type="traces",
                )
            except Exception as e:
                storage_metrics.record_storage_error(
                    operation="store_traces",
                    error_type=type(e).__name__,
                    attributes={"batch_size": len(spans_to_insert)},
                )
                logging.error(f"Error storing traces: {e}")
                raise

        otel_span.set_attribute("db.spans_inserted", len(spans_to_insert))
        return len(spans_to_insert)

    def store_logs(self, resource_logs: list[dict]) -> int:
        """Store OTLP logs using autocommit for dimensions, explicit transaction for facts.

        Transaction strategy:
        1. Cache tenant_id and connection_id (one SELECT each, reused for all logs)
        2. Dimension upserts with autocommit (service)
           - Each upsert commits immediately - idempotent, multi-process safe
        3. Fact inserts in explicit transaction after dimensions committed
           - All log rows in single transaction (atomic, can rollback)

        OTLP structure (with preserving_proto_field_name=True):
        resource_logs: []
          ├─ resource: { attributes: [] }
          └─ scope_logs: []  # snake_case
              ├─ scope: {}
              └─ log_records: []  # snake_case
        """
        if not resource_logs:
            return 0

        span = trace.get_current_span()
        span.set_attribute("db.batch.resource_logs", len(resource_logs))

        # Extract resources for common dimension processing
        resources = [rl.get("resource", {}) for rl in resource_logs]

        # Process common dimensions (tenant, connection, service) in separate linked trace
        tenant_id, connection_id, unique_services = self._process_resource_dimensions(
            resources=resources,
            signal_type="logs",
            main_span=span,
        )

        logs_to_insert = []

        # Process log records using cached service IDs (no DB calls for dimensions)
        for resource_log in resource_logs:
            resource = resource_log.get("resource", {})
            resource_attrs = resource.get("attributes", [])
            resource_dict = {attr["key"]: attr.get("value") for attr in resource_attrs}

            # Extract service info to lookup cached service_id
            service_name = "unknown"
            service_namespace = None
            for attr in resource_attrs:
                if attr["key"] == "service.name":
                    value = attr.get("value", {})
                    service_name = self._extract_string_value(value) or "unknown"
                elif attr["key"] == "service.namespace":
                    value = attr.get("value", {})
                    service_namespace = self._extract_string_value(value)

            # Lookup cached service_id (no DB call)
            service_key = (service_name, service_namespace)
            service_id = unique_services[service_key]

            # Use snake_case (preserving_proto_field_name=True)
            for scope_log in resource_log.get("scope_logs", []):
                scope = scope_log.get("scope", {})

                for log_record in scope_log.get("log_records", []):
                    # IDs - convert base64 to hex
                    trace_id = log_record.get("trace_id")
                    span_id = log_record.get("span_id")
                    if trace_id:
                        trace_id = self._base64_to_hex(trace_id)
                    if span_id:
                        span_id = self._base64_to_hex(span_id)

                    # Timestamps - use snake_case
                    time_unix_nano_raw = log_record.get("time_unix_nano", "0")
                    observed_time_unix_nano_raw = log_record.get("observed_time_unix_nano")
                    time_unix_nano = int(time_unix_nano_raw) if time_unix_nano_raw else 0
                    observed_time_unix_nano = int(observed_time_unix_nano_raw) if observed_time_unix_nano_raw else None

                    # If time_unix_nano is 0 or missing, use observed_time_unix_nano or current time
                    if time_unix_nano == 0:
                        if observed_time_unix_nano:
                            time_unix_nano = observed_time_unix_nano
                        else:
                            time_unix_nano = int(time.time() * 1_000_000_000)

                    # Convert nanoseconds to timestamp + nanos_fraction
                    timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(time_unix_nano)
                    if observed_time_unix_nano:
                        observed_timestamp, observed_nanos_fraction = _nanoseconds_to_timestamp_nanos(
                            observed_time_unix_nano
                        )
                    else:
                        observed_timestamp = None
                        observed_nanos_fraction = 0

                    # Severity - use snake_case
                    severity_number = self._normalize_severity_number(log_record.get("severity_number"))
                    severity_text = log_record.get("severity_text")

                    body = log_record.get("body", {})

                    attrs_list = log_record.get("attributes", [])
                    attributes = {attr["key"]: attr.get("value") for attr in attrs_list}

                    log_obj = LogsFact(
                        tenant_id=tenant_id,
                        connection_id=connection_id,
                        trace_id=trace_id,
                        span_id=span_id,
                        timestamp=timestamp,
                        nanos_fraction=nanos_fraction,
                        observed_timestamp=observed_timestamp,
                        observed_nanos_fraction=observed_nanos_fraction,
                        severity_number=severity_number,
                        severity_text=severity_text,
                        body=body,
                        attributes=attributes,
                        resource=resource_dict,
                        scope=scope,
                        service_id=service_id,
                        flags=log_record.get("flags", 0),
                        dropped_attributes_count=log_record.get("dropped_attributes_count", 0),
                    )
                    logs_to_insert.append(log_obj)

        # Insert all facts in explicit transaction (after dimensions committed)
        if logs_to_insert:
            try:
                with Session(self.engine) as session, session.begin():  # Explicit transaction
                    session.add_all(logs_to_insert)
                    # Transaction commits at end of block
                span.add_event("logs_inserted", {"count": len(logs_to_insert)})

                # Record ingestion metrics
                storage_metrics.record_logs_ingested(
                    count=len(logs_to_insert),
                    attributes={"tenant_id": tenant_id},
                )
                storage_metrics.record_ingestion_batch_size(
                    size=len(logs_to_insert),
                    signal_type="logs",
                )
            except Exception as e:
                storage_metrics.record_storage_error(
                    operation="store_logs",
                    error_type=type(e).__name__,
                    attributes={"batch_size": len(logs_to_insert)},
                )
                logging.error(f"Error storing logs: {e}")
                raise

        span.set_attribute("db.logs_inserted", len(logs_to_insert))
        return len(logs_to_insert)

    def store_metrics(self, resource_metrics: list[dict]) -> int:
        """Store OTLP metrics using autocommit for dimensions, explicit transaction for facts.

        Transaction strategy:
        1. Cache tenant_id and connection_id (one SELECT each, reused for all metrics)
        2. Dimension upserts with autocommit (service)
           - Each upsert commits immediately - idempotent, multi-process safe
        3. Fact inserts in explicit transaction after dimensions committed
           - All metric rows in single transaction (atomic, can rollback)

        OTLP structure (with preserving_proto_field_name=True):
        resource_metrics: []
          ├─ resource: { attributes: [] }
          └─ scope_metrics: []  # snake_case
              ├─ scope: {}
              └─ metrics: []
                  └─ [gauge|sum|histogram|summary]: { data_points: [] }  # snake_case
        """
        if not resource_metrics:
            return 0

        span = trace.get_current_span()
        span.set_attribute("db.batch.resource_metrics", len(resource_metrics))

        # Extract resources for common dimension processing
        resources = [rm.get("resource", {}) for rm in resource_metrics]

        # Process common dimensions (tenant, connection, service) in separate linked trace
        tenant_id, connection_id, unique_services = self._process_resource_dimensions(
            resources=resources,
            signal_type="metrics",
            main_span=span,
        )

        metrics_to_insert = []

        # Process metrics using cached service IDs (no DB calls for dimensions)
        for resource_metric in resource_metrics:
            resource = resource_metric.get("resource", {})
            resource_attrs_list = resource.get("attributes", [])
            resource_dict = {attr["key"]: attr.get("value") for attr in resource_attrs_list}

            # Extract service info to lookup cached service_id
            service_name = "unknown"
            service_namespace = None
            for attr in resource_attrs_list:
                if attr["key"] == "service.name":
                    value = attr.get("value", {})
                    service_name = self._extract_string_value(value) or "unknown"
                elif attr["key"] == "service.namespace":
                    value = attr.get("value", {})
                    service_namespace = self._extract_string_value(value)

            # Lookup cached service_id (no DB call)
            service_key = (service_name, service_namespace)
            service_id = unique_services[service_key]

            # Use snake_case (preserving_proto_field_name=True)
            for scope_metric in resource_metric.get("scope_metrics", []):
                scope = scope_metric.get("scope", {})

                for metric in scope_metric.get("metrics", []):
                    metric_name = metric.get("name", "unknown")
                    unit = metric.get("unit", "")
                    description = metric.get("description", "")

                    metric_type = None
                    data_points_list = []
                    temporality = None
                    is_monotonic = None

                    # Use snake_case for data_points
                    if "gauge" in metric:
                        metric_type = "gauge"
                        data_points_list = metric["gauge"].get("data_points", [])
                    elif "sum" in metric:
                        metric_type = "sum"
                        sum_data = metric["sum"]
                        data_points_list = sum_data.get("data_points", [])
                        temporality_raw = sum_data.get("aggregation_temporality", "")
                        temporality = (
                            temporality_raw.replace("AGGREGATION_TEMPORALITY_", "") if temporality_raw else None
                        )
                        is_monotonic = sum_data.get("is_monotonic", False)
                    elif "histogram" in metric:
                        metric_type = "histogram"
                        histogram_data = metric["histogram"]
                        data_points_list = histogram_data.get("data_points", [])
                        temporality_raw = histogram_data.get("aggregation_temporality", "")
                        temporality = (
                            temporality_raw.replace("AGGREGATION_TEMPORALITY_", "") if temporality_raw else None
                        )

                    for dp in data_points_list:
                        # Timestamps - use snake_case
                        time_unix_nano_str = dp.get("time_unix_nano", "0")
                        time_unix_nano = int(time_unix_nano_str) if time_unix_nano_str else 0

                        start_time_unix_nano_str = dp.get("start_time_unix_nano")
                        start_time_unix_nano = int(start_time_unix_nano_str) if start_time_unix_nano_str else None

                        # Convert nanoseconds to timestamp + nanos_fraction
                        timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(time_unix_nano)
                        if start_time_unix_nano:
                            start_timestamp, start_nanos_fraction = _nanoseconds_to_timestamp_nanos(
                                start_time_unix_nano
                            )
                        else:
                            start_timestamp = None
                            start_nanos_fraction = 0

                        dp_attrs_list = dp.get("attributes", [])
                        dp_attributes = {attr["key"]: attr.get("value") for attr in dp_attrs_list}

                        metric_obj = MetricsFact(
                            tenant_id=tenant_id,
                            connection_id=connection_id,
                            metric_name=metric_name,
                            metric_type=metric_type,
                            unit=unit,
                            description=description,
                            timestamp=timestamp,
                            nanos_fraction=nanos_fraction,
                            start_timestamp=start_timestamp,
                            start_nanos_fraction=start_nanos_fraction,
                            resource=resource_dict,
                            scope=scope,
                            attributes=dp_attributes,
                            data_points=dp,
                            temporality=temporality,
                            is_monotonic=is_monotonic,
                            service_id=service_id,
                        )
                        metrics_to_insert.append(metric_obj)

        # Insert all facts in explicit transaction (after dimensions committed)
        if metrics_to_insert:
            try:
                with Session(self.engine) as session, session.begin():  # Explicit transaction
                    session.add_all(metrics_to_insert)
                    # Transaction commits at end of block
                span.add_event("metrics_inserted", {"count": len(metrics_to_insert)})

                # Record ingestion metrics
                storage_metrics.record_metrics_ingested(
                    count=len(metrics_to_insert),
                    attributes={"tenant_id": tenant_id},
                )
                storage_metrics.record_ingestion_batch_size(
                    size=len(metrics_to_insert),
                    signal_type="metrics",
                )
            except Exception as e:
                storage_metrics.record_storage_error(
                    operation="store_metrics",
                    error_type=type(e).__name__,
                    attributes={"batch_size": len(metrics_to_insert)},
                )
                logging.error(f"Error storing metrics: {e}")
                raise

        span.set_attribute("db.metrics_inserted", len(metrics_to_insert))
        return len(metrics_to_insert)

    def search_traces(
        self,
        time_range: Any,
        filters: list | None = None,
        pagination: Any | None = None,
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """Search traces with filters and pagination using ORM."""
        query_start_time = time.time()

        if not self.engine:
            return [], False, None

        # Convert RFC3339 to timestamps
        start_ts = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
        end_ts = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            limit = pagination.limit if pagination else 100

            # ORM query for distinct trace IDs with min start time for ordering
            # Join with ServiceDim and NamespaceDim for namespace filtering

            stmt = (
                select(SpansFact.trace_id, func.min(SpansFact.start_timestamp).label("earliest_span"))
                .outerjoin(ServiceDim, SpansFact.service_id == ServiceDim.id)
                .outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
                .where(
                    SpansFact.start_timestamp >= start_ts,
                    SpansFact.start_timestamp < end_ts,
                    SpansFact.tenant_id == tenant_id,
                )
            )

            # Apply namespace filtering
            if filters:
                namespace_filters = [f for f in filters if f.field == "service_namespace"]
                if namespace_filters:
                    namespace_conditions = []
                    for f in namespace_filters:
                        if f.value == "":
                            namespace_conditions.append(ServiceDim.namespace_id.is_(None))
                        else:
                            namespace_conditions.append(NamespaceDim.namespace == f.value)
                    if namespace_conditions:
                        stmt = stmt.where(or_(*namespace_conditions))

            # Apply trace_id filtering (never NULL for spans)
            stmt, _ = self._apply_traceid_filter(SpansFact, stmt, filters)

            # Apply span_id filtering (never NULL)
            stmt, _ = self._apply_spanid_filter(SpansFact, stmt, filters)

            # Apply HTTP status filtering
            stmt, _ = self._apply_http_status_filter(stmt, filters)

            stmt = (
                stmt.group_by(SpansFact.trace_id).order_by(func.min(SpansFact.start_timestamp).desc()).limit(limit + 1)
            )

            result = session.execute(stmt)
            trace_ids = [row[0] for row in result.fetchall()]

            has_more = len(trace_ids) > limit
            if has_more:
                trace_ids = trace_ids[:limit]

            traces = []
            for trace_id in trace_ids:
                trace = self.get_trace_by_id(trace_id)
                if trace:
                    # Compute summary fields for trace list view
                    trace = self._compute_trace_summary(trace)
                    traces.append(trace)

            # Record query latency
            duration_ms = (time.time() - query_start_time) * 1000
            storage_metrics.record_query_latency(
                duration_ms=duration_ms,
                operation="search_traces",
                attributes={"result_count": len(traces), "has_more": has_more},
            )

            return traces, has_more, None

    def get_trace_by_id(self, trace_id: str) -> dict[str, Any] | None:
        """Get trace by ID with all spans using ORM."""
        query_start_time = time.time()

        if not self.engine:
            return None

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            # ORM query with outer join to ServiceDim
            # Use distinct(SpansFact.id) to deduplicate on span primary key
            # This handles cases where ServiceDim has multiple records per service_id
            stmt = (
                select(SpansFact, ServiceDim.name)
                .outerjoin(ServiceDim, SpansFact.service_id == ServiceDim.id)
                .where(
                    SpansFact.trace_id == trace_id,
                    SpansFact.tenant_id == tenant_id,
                )
                .distinct(SpansFact.id)
                .order_by(SpansFact.id, SpansFact.start_timestamp.asc())
            )

            result = session.execute(stmt)
            rows = result.fetchall()

            if not rows:
                return None

            spans = []
            for span, service_name in rows:
                # Convert timestamps to RFC3339
                start_time = _timestamp_to_rfc3339(span.start_timestamp, span.start_nanos_fraction)
                end_time = _timestamp_to_rfc3339(span.end_timestamp, span.end_nanos_fraction)
                duration_seconds = _calculate_duration_seconds(
                    span.start_timestamp, span.start_nanos_fraction, span.end_timestamp, span.end_nanos_fraction
                )

                span_dict = {
                    "trace_id": self._bytes_to_hex(span.trace_id),
                    "span_id": self._bytes_to_hex(span.span_id),
                    "parent_span_id": self._bytes_to_hex(span.parent_span_id),
                    "name": span.name,
                    "kind": span.kind,
                    "status": {"code": span.status_code, "message": span.status_message}
                    if span.status_code is not None
                    else None,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_seconds": duration_seconds,
                    "attributes": span.attributes if span.attributes else {},
                    "events": span.events if span.events else [],
                    "links": span.links if span.links else [],
                    "service_name": service_name,
                    "resource": span.resource if span.resource else {},
                }
                spans.append(span_dict)

            # Record query latency
            duration_ms = (time.time() - query_start_time) * 1000
            storage_metrics.record_query_latency(
                duration_ms=duration_ms,
                operation="get_trace_by_id",
                attributes={"span_count": len(spans), "trace_id": trace_id},
            )

            return {"trace_id": trace_id, "spans": spans}

    def _compute_trace_summary(self, trace: dict[str, Any]) -> dict[str, Any]:
        """Compute summary fields for a trace from its spans."""
        if not trace or not trace.get("spans"):
            return trace

        spans = trace["spans"]
        if not spans:
            return trace

        # Find root span (no parent_span_id or first span)
        root_span = next((s for s in spans if not s.get("parent_span_id") or s["parent_span_id"] == "0" * 16), spans[0])

        # Helper to safely extract string value from attribute (handle nested objects)
        def get_attr_str(attrs: dict, *keys: str) -> str:
            for key in keys:
                value = attrs.get(key)
                if value is not None:
                    # Handle case where value is a dict with nested structure
                    if isinstance(value, dict):
                        # Try common nested keys (OpenTelemetry format with underscores)
                        if "string_value" in value:
                            return str(value["string_value"])
                        if "int_value" in value:
                            return str(value["int_value"])
                        if "bool_value" in value:
                            return str(value["bool_value"])
                        if "double_value" in value:
                            return str(value["double_value"])
                        # Try camelCase variants (legacy/alternative format)
                        if "stringValue" in value:
                            return str(value["stringValue"])
                        if "intValue" in value:
                            return str(value["intValue"])
                        if "value" in value:
                            return str(value["value"])
                        # If still a dict, skip it
                        continue
                    return str(value)
            return ""

        # Extract root span metadata
        root_attrs = root_span.get("attributes", {})
        trace["service_name"] = root_span.get("service_name")
        trace["root_span_name"] = root_span.get("name")
        trace["root_span_method"] = get_attr_str(root_attrs, "http.method", "http.request.method")

        # Prioritize http.url first, then http.route, then fall back to name
        http_url = get_attr_str(root_attrs, "http.url", "url.full")
        http_route = get_attr_str(root_attrs, "http.route")
        trace["root_span_url"] = http_url
        trace["root_span_route"] = http_route

        # Set target based on priority: url > route > target attribute
        if http_url:
            # Extract path from full URL
            try:
                parsed = urlparse(http_url)
                trace["root_span_target"] = parsed.path or "/"
            except Exception:
                trace["root_span_target"] = http_url
        elif http_route:
            trace["root_span_target"] = http_route
        else:
            trace["root_span_target"] = get_attr_str(root_attrs, "http.target", "url.path")

        trace["root_span_host"] = get_attr_str(root_attrs, "http.host", "net.host.name", "server.address")
        trace["root_span_scheme"] = get_attr_str(root_attrs, "http.scheme", "url.scheme")
        trace["root_span_server_name"] = get_attr_str(root_attrs, "server.address", "net.host.name")

        # Extract status code from root span attributes (not from status object)
        status_code_str = get_attr_str(root_attrs, "http.status_code", "http.response.status_code")
        if status_code_str:
            try:
                trace["root_span_status_code"] = int(status_code_str)
            except (ValueError, TypeError):
                trace["root_span_status_code"] = None
        else:
            trace["root_span_status_code"] = None

        # Keep status object for error detection
        root_status = root_span.get("status")
        if root_status:
            trace["root_span_status"] = root_status

        # Compute trace-level aggregates
        trace["start_time"] = min(s["start_time"] for s in spans)
        trace["end_time"] = max(s["end_time"] for s in spans)
        trace["span_count"] = len(spans)

        # Calculate total duration from earliest start to latest end
        start_dt = datetime.fromisoformat(trace["start_time"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(trace["end_time"].replace("Z", "+00:00"))
        trace["duration_seconds"] = (end_dt - start_dt).total_seconds()

        return trace

    def search_spans(
        self,
        time_range: Any,
        filters: list | None = None,
        pagination: Any | None = None,
    ) -> tuple[list, bool, str | None]:
        """Search spans with filters and pagination using ORM."""
        if not self.engine:
            return [], False, None

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            limit = pagination.limit if pagination else 100

            # ORM query with JOIN to ServiceDim and NamespaceDim
            # Use distinct(SpansFact.id) to deduplicate on span primary key
            stmt = (
                select(SpansFact, ServiceDim.name, NamespaceDim.namespace)
                .outerjoin(ServiceDim, SpansFact.service_id == ServiceDim.id)
                .outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
            )

            # Apply namespace filtering
            if filters:
                namespace_filters = [f for f in filters if f.field == "service_namespace"]
                if namespace_filters:
                    namespace_conditions = []
                    for f in namespace_filters:
                        if f.value == "":
                            namespace_conditions.append(ServiceDim.namespace_id.is_(None))
                        else:
                            namespace_conditions.append(NamespaceDim.namespace == f.value)
                    if namespace_conditions:
                        stmt = stmt.where(or_(*namespace_conditions))

            # Apply trace_id filtering (never NULL for spans)
            stmt, _ = self._apply_traceid_filter(SpansFact, stmt, filters)

            # Apply span_id filtering (never NULL)
            stmt, _ = self._apply_spanid_filter(SpansFact, stmt, filters)

            # Apply HTTP status filtering
            stmt, _ = self._apply_http_status_filter(stmt, filters)

            # Convert RFC3339 to timestamps
            start_timestamp = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
            end_timestamp = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))

            stmt = stmt.where(
                SpansFact.start_timestamp >= start_timestamp,
                SpansFact.start_timestamp < end_timestamp,
                SpansFact.tenant_id == tenant_id,
            )

            # Apply other filters (non-namespace, non-traceid, non-spanid, non-http_status)
            if filters:
                excluded_fields = {"service_namespace", "trace_id", "span_id", "http_status"}
                for f in filters:
                    if f.field in excluded_fields:
                        continue  # Already handled by filter helpers
                    elif f.field == "service_name":
                        if f.operator == "equals":
                            stmt = stmt.where(ServiceDim.name == f.value)
                        elif f.operator == "contains":
                            stmt = stmt.where(ServiceDim.name.contains(f.value))

            stmt = stmt.distinct(SpansFact.id).order_by(SpansFact.id, SpansFact.start_timestamp.desc()).limit(limit + 1)

            result = session.execute(stmt)
            rows = result.fetchall()

            has_more = len(rows) > limit
            if has_more:
                rows = rows[:limit]

            spans = []
            for span, service_name, service_namespace in rows:
                # Convert attributes dict to list of {key, value} pairs for API model
                attributes_dict = span.attributes if span.attributes else {}
                attributes_list = []
                for key, value in attributes_dict.items():
                    attributes_list.append(SpanAttribute(key=key, value=value))

                # Convert timestamps to RFC3339
                start_time = _timestamp_to_rfc3339(span.start_timestamp, span.start_nanos_fraction)
                end_time = _timestamp_to_rfc3339(span.end_timestamp, span.end_nanos_fraction)
                duration_seconds = _calculate_duration_seconds(
                    span.start_timestamp, span.start_nanos_fraction, span.end_timestamp, span.end_nanos_fraction
                )

                # Convert events from JSONB dict format to SpanEvent models
                events_list = []
                if span.events:
                    for event_dict in span.events:
                        # Convert event attributes (stored as list of dicts with key/value)
                        event_attrs = []
                        if event_dict.get("attributes"):
                            attrs = event_dict["attributes"]
                            if isinstance(attrs, list):
                                # OTLP format: list of {key: "name", value: "val"}
                                for attr in attrs:
                                    event_attrs.append(
                                        SpanAttribute(key=attr.get("key", ""), value=attr.get("value", ""))
                                    )
                            elif isinstance(attrs, dict):
                                # Dict format: {key: value}
                                for key, value in attrs.items():
                                    event_attrs.append(SpanAttribute(key=key, value=value))

                        events_list.append(
                            SpanEvent(
                                name=event_dict.get("name", ""),
                                timestamp=event_dict.get("timestamp", ""),
                                attributes=event_attrs if event_attrs else None,
                            )
                        )

                # Convert links from JSONB dict format to SpanLink models
                links_list = []
                if span.links:
                    for link_dict in span.links:
                        # Convert link attributes (stored as list of dicts with key/value)
                        link_attrs = []
                        if link_dict.get("attributes"):
                            attrs = link_dict["attributes"]
                            if isinstance(attrs, list):
                                # OTLP format: list of {key: "name", value: "val"}
                                for attr in attrs:
                                    link_attrs.append(
                                        SpanAttribute(key=attr.get("key", ""), value=attr.get("value", ""))
                                    )
                            elif isinstance(attrs, dict):
                                # Dict format: {key: value}
                                for key, value in attrs.items():
                                    link_attrs.append(SpanAttribute(key=key, value=value))

                        links_list.append(
                            SpanLink(
                                trace_id=link_dict.get("trace_id", ""),
                                span_id=link_dict.get("span_id", ""),
                                attributes=link_attrs if link_attrs else None,
                            )
                        )

                span_obj = Span(
                    trace_id=self._bytes_to_hex(span.trace_id),
                    span_id=self._bytes_to_hex(span.span_id),
                    parent_span_id=self._bytes_to_hex(span.parent_span_id) if span.parent_span_id else None,
                    name=span.name,
                    kind=span.kind,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration_seconds,
                    attributes=attributes_list,
                    events=events_list if events_list else None,
                    links=links_list if links_list else None,
                    status={"code": span.status_code, "message": span.status_message}
                    if span.status_code is not None
                    else None,
                    resource=span.resource if span.resource else {},
                    service_name=service_name,
                    service_namespace=service_namespace,
                    scope=span.scope if span.scope else None,
                )
                spans.append(span_obj)

            return spans, has_more, None

    def search_logs(
        self,
        time_range: Any,
        filters: list | None = None,
        pagination: Any | None = None,
    ) -> tuple[list, bool, str | None]:
        """Search logs with filters and pagination using ORM."""
        if not self.engine:
            return [], False, None

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            limit = pagination.limit if pagination else 100

            # ORM query with JOIN to ServiceDim (NamespaceDim JOIN handled by _apply_namespace_filtering)
            stmt = select(LogsFact, ServiceDim.name, NamespaceDim.namespace).outerjoin(
                ServiceDim, LogsFact.service_id == ServiceDim.id
            )

            # Apply namespace filtering with proper JOIN strategy (adds NamespaceDim JOIN)
            stmt, _ = self._apply_namespace_filtering(stmt, filters)

            # Apply trace_id filtering (NULL is valid for logs)
            stmt, _ = self._apply_traceid_filter(LogsFact, stmt, filters)

            # Apply span_id filtering (never NULL)
            stmt, _ = self._apply_spanid_filter(LogsFact, stmt, filters)

            # Apply log level filtering using severity_number ranges
            stmt, _ = self._apply_log_level_filter(stmt, filters)

            # Convert RFC3339 strings to timestamps for query
            start_timestamp = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
            end_timestamp = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))

            stmt = stmt.where(
                LogsFact.timestamp >= start_timestamp,
                LogsFact.timestamp < end_timestamp,
                LogsFact.tenant_id == tenant_id,
            )

            # Apply other filters (non-namespace, non-traceid, non-spanid, non-log_level)
            if filters:
                excluded_fields = {"service_namespace", "trace_id", "span_id", "log_level"}
                for f in filters:
                    if f.field in excluded_fields:
                        continue  # Already handled by filter helpers
                    elif f.field == "service_name":
                        if f.operator == "equals":
                            stmt = stmt.where(ServiceDim.name == f.value)
                        elif f.operator == "contains":
                            stmt = stmt.where(ServiceDim.name.contains(f.value))

            stmt = stmt.order_by(LogsFact.timestamp.desc()).limit(limit + 1)

            result = session.execute(stmt)
            rows = result.fetchall()

            has_more = len(rows) > limit
            if has_more:
                rows = rows[:limit]

            logs = []
            for log, service_name, service_namespace in rows:
                # Extract body string per OTLP spec: body.stringValue
                body = log.body
                if isinstance(body, dict):
                    body_text = body.get("stringValue", body.get("string_value", str(body)))
                else:
                    body_text = str(body) if body else ""

                # Convert attributes dict to list of {key, value} pairs for API model
                attributes_dict = log.attributes if log.attributes else {}
                attributes_list = []
                for key, value in attributes_dict.items():
                    attributes_list.append({"key": key, "value": value})

                # Convert timestamps to RFC3339
                timestamp = _timestamp_to_rfc3339(log.timestamp, log.nanos_fraction)
                observed_timestamp = (
                    _timestamp_to_rfc3339(log.observed_timestamp, log.observed_nanos_fraction)
                    if log.observed_timestamp
                    else None
                )

                log_record = LogRecord(
                    log_id=str(log.id),
                    timestamp=timestamp,
                    observed_timestamp=observed_timestamp,
                    severity_number=log.severity_number,
                    severity_text=log.severity_text,
                    body=body_text,
                    attributes=attributes_list,
                    trace_id=log.trace_id,
                    span_id=log.span_id,
                    service_name=service_name,
                    service_namespace=service_namespace,
                    resource=log.resource if log.resource else {},
                )
                logs.append(log_record)

            return logs, has_more, None

    def search_metrics(
        self,
        time_range: Any,
        metric_names: list[str] | None = None,
        filters: list | None = None,
        pagination: Any | None = None,
    ) -> tuple[list, bool, str | None]:
        """Search metrics with filters and pagination using ORM."""
        if not self.engine:
            return [], False, None

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            limit = pagination.limit if pagination else 100

            # ORM query with JOIN to ServiceDim and NamespaceDim
            # Use distinct(MetricsFact.id) to deduplicate on metric primary key
            stmt = (
                select(MetricsFact, ServiceDim.name, NamespaceDim.namespace)
                .outerjoin(ServiceDim, MetricsFact.service_id == ServiceDim.id)
                .outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
            )

            # Apply namespace filtering
            if filters:
                namespace_filters = [f for f in filters if f.field == "service_namespace"]
                if namespace_filters:
                    namespace_conditions = []
                    for f in namespace_filters:
                        if f.value == "":
                            namespace_conditions.append(ServiceDim.namespace_id.is_(None))
                        else:
                            namespace_conditions.append(NamespaceDim.namespace == f.value)
                    if namespace_conditions:
                        stmt = stmt.where(or_(*namespace_conditions))

            # Convert RFC3339 to timestamps
            start_timestamp = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
            end_timestamp = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))

            stmt = stmt.where(
                MetricsFact.timestamp >= start_timestamp,
                MetricsFact.timestamp < end_timestamp,
                MetricsFact.tenant_id == tenant_id,
            )

            if metric_names:
                stmt = stmt.where(MetricsFact.metric_name.in_(metric_names))

            # Apply other filters (non-namespace)
            if filters:
                for f in filters:
                    if f.field == "service_namespace":
                        continue  # Already handled by _apply_namespace_filtering
                    elif f.field == "service_name":
                        if f.operator == "equals":
                            stmt = stmt.where(ServiceDim.name == f.value)
                        elif f.operator == "contains":
                            stmt = stmt.where(ServiceDim.name.contains(f.value))

            stmt = stmt.distinct(MetricsFact.id).order_by(MetricsFact.id, MetricsFact.timestamp.desc()).limit(limit + 1)

            result = session.execute(stmt)
            rows = result.fetchall()

            has_more = len(rows) > limit
            if has_more:
                rows = rows[:limit]

            # Aggregate metrics by name for catalog view
            metrics_by_name = {}
            for m, service_name, service_namespace in rows:
                metric_name = m.metric_name

                if metric_name not in metrics_by_name:
                    # Convert timestamp back to nanoseconds for API
                    timestamp_ns = _timestamp_nanos_to_nanoseconds(m.timestamp, m.nanos_fraction)

                    # Wrap data_points in list if it's a dict (single data point)
                    data_points = m.data_points if m.data_points else []
                    if isinstance(data_points, dict):
                        data_points = [data_points]

                    metrics_by_name[metric_name] = {
                        "metric": Metric(
                            metric_id=str(m.id),
                            name=m.metric_name,
                            description=m.description,
                            unit=m.unit,
                            metric_type=m.metric_type,
                            aggregation_temporality=m.temporality,
                            timestamp_ns=timestamp_ns,
                            data_points=data_points,
                            attributes=m.attributes if m.attributes else {},
                            service_name=service_name,
                            service_namespace=service_namespace,
                            resource=m.resource if m.resource else {},
                            value=0.0,
                            exemplars=[],
                        ),
                        "resources": set(),
                        "attribute_keys": set(),
                        "attribute_combos": set(),
                    }

                # Track unique resources
                if m.resource:
                    resource_hash = hashlib.md5(json.dumps(m.resource, sort_keys=True).encode()).hexdigest()
                    metrics_by_name[metric_name]["resources"].add(resource_hash)

                # Track unique attribute combinations
                if m.attributes:
                    attr_hash = hashlib.md5(json.dumps(m.attributes, sort_keys=True).encode()).hexdigest()
                    metrics_by_name[metric_name]["attribute_combos"].add(attr_hash)
                    # Track attribute keys
                    for key in m.attributes:
                        metrics_by_name[metric_name]["attribute_keys"].add(key)

            # Build final metrics list with aggregated stats
            metrics = []
            for _metric_name, data in metrics_by_name.items():
                metric = data["metric"]
                # Add aggregation stats as dict fields (Pydantic allows extra fields)
                metric_dict = metric.model_dump()
                metric_dict["resource_count"] = len(data["resources"])
                metric_dict["label_count"] = len(data["attribute_keys"])
                metric_dict["attribute_combinations"] = len(data["attribute_combos"])
                metrics.append(Metric(**metric_dict))

            return metrics, has_more, None

    def get_metric_detail(
        self, metric_name: str, time_range: Any, filters: list | None = None, include_attributes: bool = False
    ) -> dict | None:
        """Get detailed time-series data for a specific metric.

        Returns data in format expected by UI:
        {
            "name": "metric_name",
            "type": "gauge|sum|histogram",
            "unit": "unit",
            "description": "description",
            "series": [...],
            "attributes": [...]  # Only when include_attributes=True
        }
        """
        if not self.engine:
            return None

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            # Parse time range
            start_ts, _start_nanos = _rfc3339_to_timestamp_nanos(time_range.start_time)
            end_ts, _end_nanos = _rfc3339_to_timestamp_nanos(time_range.end_time)

            # Build base query
            stmt = (
                select(
                    MetricsFact,
                    ServiceDim.name.label("service_name"),
                    NamespaceDim.namespace.label("service_namespace"),
                )
                .join(ServiceDim, MetricsFact.service_id == ServiceDim.id)
                .outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
                .where(
                    MetricsFact.tenant_id == tenant_id,
                    MetricsFact.metric_name == metric_name,
                    MetricsFact.timestamp >= start_ts,
                    MetricsFact.timestamp <= end_ts,
                )
            )

            # Apply namespace filters if provided
            if filters:
                namespace_filter_values = []
                for f in filters:
                    if f.field == "namespace" and f.operator == "equals":
                        namespace_filter_values.append(f.value)

                if namespace_filter_values:
                    namespace_ids = []
                    for ns_name in namespace_filter_values:
                        ns_stmt = select(NamespaceDim.id).where(
                            NamespaceDim.tenant_id == tenant_id, NamespaceDim.namespace == ns_name
                        )
                        ns_result = session.execute(ns_stmt)
                        ns_row = ns_result.first()
                        if ns_row:
                            namespace_ids.append(ns_row[0])

                    if namespace_ids:
                        stmt = stmt.where(ServiceDim.namespace_id.in_(namespace_ids))

            stmt = stmt.order_by(MetricsFact.timestamp.asc())

            result = session.execute(stmt)
            rows = result.all()

            if not rows:
                return None

            # Get first row for metadata
            first_metric = rows[0][0]

            # Group data points by attribute combination
            series_map = {}
            for m, service_name, service_namespace in rows:
                # Create series key from attributes
                attr_hash = hashlib.md5(json.dumps(m.attributes or {}, sort_keys=True).encode()).hexdigest()

                if attr_hash not in series_map:
                    # Create label from attributes
                    if m.attributes:
                        label_parts = [f"{k}={v}" for k, v in sorted(m.attributes.items())]
                        label = ", ".join(label_parts)
                    else:
                        label = service_name or "default"

                    # Build resource attributes from service metadata and OTLP resource
                    resource = {}
                    if service_name:
                        resource["service.name"] = service_name
                    if service_namespace:
                        resource["service.namespace"] = service_namespace
                    # Add OTLP resource if present
                    if m.resource:
                        resource.update(m.resource)

                    series_map[attr_hash] = {
                        "label": label,
                        "attributes": m.attributes or {},
                        "resource": resource,
                        "datapoints": [],
                    }

                # Add datapoint
                timestamp_rfc = _timestamp_to_rfc3339(m.timestamp, m.nanos_fraction)

                # Extract value from data_points (OTLP format)
                value = 0.0
                if m.data_points:
                    dp_to_check = None
                    if isinstance(m.data_points, dict):
                        dp_to_check = m.data_points
                    elif isinstance(m.data_points, list) and len(m.data_points) > 0:
                        dp_to_check = m.data_points[0]

                    if dp_to_check and isinstance(dp_to_check, dict):
                        # OTLP data point value fields
                        if "as_double" in dp_to_check:
                            value = float(dp_to_check["as_double"])
                        elif "as_int" in dp_to_check:
                            value = float(dp_to_check["as_int"])
                        # Fallback to simple fields
                        elif "value" in dp_to_check:
                            value = float(dp_to_check["value"])
                        elif "sum" in dp_to_check:
                            value = float(dp_to_check["sum"])
                        elif "count" in dp_to_check:
                            value = float(dp_to_check["count"])

                series_map[attr_hash]["datapoints"].append({"timestamp": timestamp_rfc, "value": value})

            # Convert series map to list
            series = list(series_map.values())

            result_dict = {
                "name": metric_name,
                "type": first_metric.metric_type or "gauge",
                "unit": first_metric.unit or "",
                "description": first_metric.description or "",
                "series": series,
            }

            # Include unique attributes if requested (for cardinality explorer)
            if include_attributes:
                # Query for distinct attribute combinations
                attr_stmt = (
                    select(distinct(MetricsFact.attributes))
                    .where(MetricsFact.tenant_id == tenant_id, MetricsFact.metric_name == metric_name)
                    .order_by(MetricsFact.attributes)
                )
                attr_result = session.execute(attr_stmt)
                attr_rows = attr_result.scalars().all()
                # Filter out None and return list of attribute dicts
                result_dict["attributes"] = [attrs for attrs in attr_rows if attrs is not None]

            return result_dict

    def get_services(self, time_range: Any | None = None, filters: list | None = None) -> list:
        """Get service catalog with RED metrics using ORM."""
        if not self.engine:
            return []

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            # ORM query with aggregations
            stmt = (
                select(
                    ServiceDim.name,
                    NamespaceDim.namespace,
                    func.count().label("request_count"),
                    func.count().filter(SpansFact.status_code == 2).label("error_count"),
                    # Duration in microseconds: EXTRACT(EPOCH FROM end_timestamp - start_timestamp) * 1000000 + (end_nanos_fraction - start_nanos_fraction) / 1000
                    func.percentile_cont(0.50)
                    .within_group(
                        func.extract("epoch", SpansFact.end_timestamp - SpansFact.start_timestamp) * 1000000
                        + (SpansFact.end_nanos_fraction - SpansFact.start_nanos_fraction) / 1000
                    )
                    .label("p50_micros"),
                    func.percentile_cont(0.95)
                    .within_group(
                        func.extract("epoch", SpansFact.end_timestamp - SpansFact.start_timestamp) * 1000000
                        + (SpansFact.end_nanos_fraction - SpansFact.start_nanos_fraction) / 1000
                    )
                    .label("p95_micros"),
                    func.min(SpansFact.start_timestamp).label("first_seen_ts"),
                    func.max(SpansFact.start_timestamp).label("last_seen_ts"),
                )
                .select_from(SpansFact)
                .join(ServiceDim, SpansFact.service_id == ServiceDim.id)
                .outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)
                .where(SpansFact.tenant_id == tenant_id)
            )

            # Apply namespace filtering - if namespace filters exist, only show those namespaces
            if filters:
                namespace_filters = [f for f in filters if f.field == "service_namespace"]
                if namespace_filters:
                    namespace_values = []
                    has_empty_namespace = False
                    for f in namespace_filters:
                        if f.value == "":
                            has_empty_namespace = True
                        else:
                            namespace_values.append(f.value)

                    namespace_conditions = []
                    if namespace_values:
                        namespace_conditions.append(NamespaceDim.namespace.in_(namespace_values))
                    if has_empty_namespace:
                        namespace_conditions.append(ServiceDim.namespace_id.is_(None))

                    if namespace_conditions:
                        stmt = stmt.where(or_(*namespace_conditions))

            if time_range:
                start_timestamp = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
                end_timestamp = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))
                stmt = stmt.where(
                    SpansFact.start_timestamp >= start_timestamp,
                    SpansFact.start_timestamp < end_timestamp,
                )

            stmt = stmt.group_by(ServiceDim.name, NamespaceDim.namespace).order_by(func.count().desc())

            result = session.execute(stmt)
            rows = result.fetchall()

            services = []
            for row in rows:
                error_rate = (row.error_count / row.request_count) * 100 if row.request_count > 0 else 0.0

                service = Service(
                    name=row.name,
                    namespace=row.namespace,
                    request_count=row.request_count,
                    error_count=row.error_count,
                    error_rate=round(error_rate, 2),
                    # Convert microseconds to milliseconds
                    p50_latency_ms=round(row.p50_micros / 1_000, 2) if row.p50_micros else 0.0,
                    p95_latency_ms=round(row.p95_micros / 1_000, 2) if row.p95_micros else 0.0,
                    # Convert timestamp to nanoseconds for API compatibility
                    first_seen=_timestamp_nanos_to_nanoseconds(row.first_seen_ts, 0),
                    last_seen=_timestamp_nanos_to_nanoseconds(row.last_seen_ts, 0),
                )
                services.append(service)

            return services

    def get_service_map(self, time_range: Any | None = None, filters: list | None = None) -> tuple[list, list]:
        """Get service dependency map from spans using ORM.

        Builds service map edges based on OpenTelemetry span kinds:
        - CLIENT (3): Extract target from peer.service, server.address, or http.url → edge: client → target
        - PRODUCER (4): Extract messaging.destination → edge: producer → queue/topic
        - CONSUMER (5): Extract messaging.source → edge: queue/topic → consumer (reversed!)
        - SERVER (2), INTERNAL (1), UNSPECIFIED (0): Use parent-child relationships

        Node types determined from span attributes:
        - database: spans with db.system attribute
        - messaging: spans with messaging.system attribute
        - service: default for services
        """
        if not self.engine:
            return [], []

        # Convert RFC3339 to timestamps
        if not time_range:
            # Default to last 30 minutes if no time range provided
            end_ts = datetime.now(UTC)
            start_ts = end_ts - timedelta(minutes=30)
        else:
            start_ts = datetime.fromisoformat(time_range.start_time.replace("Z", "+00:00"))
            end_ts = datetime.fromisoformat(time_range.end_time.replace("Z", "+00:00"))

        with Session(self.engine) as session:
            # Get the unknown tenant_id
            tenant_id = self._get_unknown_tenant_id()

            # Query all spans in time range with their attributes to determine node types
            stmt = (
                select(
                    SpansFact.span_id,
                    SpansFact.parent_span_id,
                    SpansFact.trace_id,
                    SpansFact.kind,
                    SpansFact.attributes,
                    SpansFact.start_timestamp,
                    SpansFact.end_timestamp,
                    ServiceDim.name.label("service_name"),
                )
                .join(ServiceDim, SpansFact.service_id == ServiceDim.id)
                .where(
                    SpansFact.start_timestamp >= start_ts,
                    SpansFact.start_timestamp < end_ts,
                    SpansFact.tenant_id == tenant_id,
                )
            )

            # Apply namespace filtering
            if filters:
                namespace_filters = [f for f in filters if f.field == "service_namespace"]
                if namespace_filters:
                    stmt = stmt.outerjoin(NamespaceDim, ServiceDim.namespace_id == NamespaceDim.id)

                    namespace_values = []
                    has_empty_namespace = False
                    for f in namespace_filters:
                        if f.value == "":
                            has_empty_namespace = True
                        else:
                            namespace_values.append(f.value)

                    conditions = []
                    if namespace_values:
                        conditions.append(NamespaceDim.namespace.in_(namespace_values))
                    if has_empty_namespace:
                        conditions.append(ServiceDim.namespace_id.is_(None))

                    if conditions:
                        stmt = stmt.where(or_(*conditions))

            result = session.execute(stmt)
            spans = result.fetchall()

            # Build span lookup map
            span_map = {}
            for span_row in spans:
                span_map[span_row.span_id] = {
                    "span_id": span_row.span_id,
                    "parent_span_id": span_row.parent_span_id,
                    "trace_id": span_row.trace_id,
                    "kind": span_row.kind,
                    "attributes": span_row.attributes or {},
                    "start_timestamp": span_row.start_timestamp,
                    "end_timestamp": span_row.end_timestamp,
                    "service_name": span_row.service_name,
                }

            nodes_dict = {}
            edges_dict = {}  # Stores {edge_key: {"count": N, "durations": []}}

            # Helper function to extract value from OTel attribute dict
            def extract_attr_value(attr_value):
                """Extract actual value from OpenTelemetry attribute value dict."""
                if attr_value is None:
                    return None
                if isinstance(attr_value, dict):
                    # OTel attribute values are like {"string_value": "actual_value"}
                    return attr_value.get("string_value") or attr_value.get("int_value") or attr_value.get("bool_value")
                return attr_value

            # Process each span to build nodes and edges
            for span_data in span_map.values():
                service = str(span_data["service_name"])  # Ensure string
                attributes = span_data["attributes"]
                span_kind = span_data.get(
                    "kind", 0
                )  # 0=UNSPECIFIED, 1=INTERNAL, 2=SERVER, 3=CLIENT, 4=PRODUCER, 5=CONSUMER

                # Calculate span duration in milliseconds
                duration_ms = None
                if span_data.get("end_timestamp") and span_data.get("start_timestamp"):
                    duration_ns = (
                        span_data["end_timestamp"] - span_data["start_timestamp"]
                    ).total_seconds() * 1_000_000_000
                    duration_ms = duration_ns / 1_000_000

                # Ensure service node exists
                if service not in nodes_dict:
                    nodes_dict[service] = {"type": "service"}

                # Handle CLIENT spans (kind=3): outgoing calls from this service
                # Create edges based on target extraction, not parent-child relationships
                if span_kind == 3:  # CLIENT
                    target_service = None

                    # Check for database client calls
                    db_system = extract_attr_value(attributes.get("db.system"))
                    if db_system:
                        db_name = extract_attr_value(attributes.get("db.name"))
                        if db_name:
                            target_service = str(db_name)
                            if target_service not in nodes_dict:
                                nodes_dict[target_service] = {"type": "database", "db_system": str(db_system)}

                    # Check for HTTP client calls - extract target service from attributes
                    if not target_service:
                        # Try peer.service first (recommended OTel attribute for target service)
                        peer_service = extract_attr_value(attributes.get("peer.service"))
                        if peer_service:
                            target_service = str(peer_service)
                        else:
                            # Try to extract from server.address or net.peer.name
                            server_address = extract_attr_value(attributes.get("server.address")) or extract_attr_value(
                                attributes.get("net.peer.name")
                            )
                            if server_address:
                                # Use hostname as target service (strip port if present)
                                target_service = str(server_address).split(":")[0]
                            else:
                                # Last resort: try to extract from http.url
                                http_url = extract_attr_value(attributes.get("http.url")) or extract_attr_value(
                                    attributes.get("url.full")
                                )
                                if http_url:
                                    # Parse hostname from URL
                                    try:
                                        parsed = urlparse(str(http_url))
                                        if parsed.hostname:
                                            target_service = parsed.hostname
                                    except Exception:
                                        pass

                    # Create edge from client to target
                    if target_service:
                        # Ensure target service node exists (if not already a database node)
                        if target_service not in nodes_dict:
                            nodes_dict[target_service] = {"type": "service"}

                        edge_key = (service, target_service)
                        if edge_key not in edges_dict:
                            edges_dict[edge_key] = {"count": 0, "durations": []}
                        edges_dict[edge_key]["count"] += 1
                        if duration_ms:
                            edges_dict[edge_key]["durations"].append(duration_ms)

                # Handle PRODUCER spans (kind=4): sending messages to queue/topic
                elif span_kind == 4:  # PRODUCER
                    messaging_system = extract_attr_value(attributes.get("messaging.system"))
                    if messaging_system:
                        dest = extract_attr_value(attributes.get("messaging.destination.name")) or extract_attr_value(
                            attributes.get("messaging.destination")
                        )
                        if dest:
                            dest = str(dest)
                            if dest not in nodes_dict:
                                nodes_dict[dest] = {"type": "messaging", "messaging_system": str(messaging_system)}
                            # Edge from producer to messaging destination
                            edge_key = (service, dest)
                            if edge_key not in edges_dict:
                                edges_dict[edge_key] = {"count": 0, "durations": []}
                            edges_dict[edge_key]["count"] += 1
                            if duration_ms:
                                edges_dict[edge_key]["durations"].append(duration_ms)

                # Handle CONSUMER spans (kind=5): receiving messages from queue/topic
                # NOTE: Edge direction is REVERSED - from messaging source to consumer
                elif span_kind == 5:  # CONSUMER
                    messaging_system = extract_attr_value(attributes.get("messaging.system"))
                    if messaging_system:
                        source = (
                            extract_attr_value(attributes.get("messaging.source.name"))
                            or extract_attr_value(attributes.get("messaging.destination.name"))
                            or extract_attr_value(attributes.get("messaging.destination"))
                        )
                        if source:
                            source = str(source)
                            if source not in nodes_dict:
                                nodes_dict[source] = {"type": "messaging", "messaging_system": str(messaging_system)}
                            # Edge from messaging source to consumer (REVERSED)
                            edge_key = (source, service)
                            if edge_key not in edges_dict:
                                edges_dict[edge_key] = {"count": 0, "durations": []}
                            edges_dict[edge_key]["count"] += 1
                            if duration_ms:
                                edges_dict[edge_key]["durations"].append(duration_ms)

                # Handle SERVER and INTERNAL spans (kind=2, 1, 0): use parent-child relationships
                else:  # SERVER, INTERNAL, or UNSPECIFIED
                    parent_span_id = span_data["parent_span_id"]
                    if parent_span_id and parent_span_id in span_map:
                        parent = span_map[parent_span_id]
                        parent_service = str(parent["service_name"])
                        parent_kind = parent.get("kind", 0)

                        # Only create edge if different services
                        # Skip if parent is CLIENT (CLIENT spans create their own edges)
                        if parent_service != service and parent_kind != 3:
                            edge_key = (parent_service, service)
                            if edge_key not in edges_dict:
                                edges_dict[edge_key] = {"count": 0, "durations": []}
                            edges_dict[edge_key]["count"] += 1
                            if duration_ms:
                                edges_dict[edge_key]["durations"].append(duration_ms)

            # Convert to API models
            nodes = [
                ServiceMapNode(
                    id=name,
                    name=name,
                    type=data["type"],
                    db_system=data.get("db_system"),
                    messaging_system=data.get("messaging_system"),
                )
                for name, data in nodes_dict.items()
            ]

            edges = [
                ServiceMapEdge(
                    source=source,
                    target=target,
                    call_count=data["count"],
                    avg_duration_ms=round(sum(data["durations"]) / len(data["durations"]), 2)
                    if data["durations"]
                    else None,
                )
                for (source, target), data in edges_dict.items()
            ]

            return nodes, edges
            nodes = [ServiceMapNode(id=name, name=name, type=data["type"]) for name, data in nodes_dict.items()]

            edges = [
                ServiceMapEdge(source=source, target=target, call_count=count)
                for (source, target), count in edges_dict.items()
            ]

            return nodes, edges
