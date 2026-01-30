"""OpenTelemetry metrics instrumentation for storage operations.

Provides centralized metrics for monitoring:
- Ingestion rates (spans/sec, logs/sec, metrics/sec)
- Query latency (histogram)
- Dimension cache hit/miss rates
- Partition health (size, age, count)
- Connection pool statistics
- Error rates by operation type
"""

import logging
from typing import Any

from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, ObservableGauge, UpDownCounter

logger = logging.getLogger(__name__)

# Get meter for ollyscale storage metrics
meter = metrics.get_meter("ollyscale.storage", version="2.0.0")

# Global metric instruments (can be reassigned for testing)
spans_ingested_counter: Counter
logs_ingested_counter: Counter
metrics_ingested_counter: Counter
ingestion_batch_size_histogram: Histogram
query_latency_histogram: Histogram
dimension_cache_ops_counter: Counter
dimension_upserts_counter: Counter
partition_count_gauge: ObservableGauge | None = None
partition_size_gauge: ObservableGauge | None = None
oldest_partition_age_gauge: ObservableGauge | None = None
connection_pool_size_gauge: UpDownCounter
storage_errors_counter: Counter


def _create_metrics() -> None:
    """Create or recreate all metric instruments.

    This function is called at module initialization and can be called
    again during testing to recreate metrics with a test meter.
    """
    global spans_ingested_counter, logs_ingested_counter, metrics_ingested_counter
    global ingestion_batch_size_histogram, query_latency_histogram
    global dimension_cache_ops_counter, dimension_upserts_counter
    global connection_pool_size_gauge, storage_errors_counter

    # ============================================================================
    # INGESTION METRICS
    # ============================================================================

    # Counters for ingestion volume
    spans_ingested_counter = meter.create_counter(
        name="storage.spans.ingested",
        description="Total number of spans ingested into storage",
        unit="spans",
    )

    logs_ingested_counter = meter.create_counter(
        name="storage.logs.ingested",
        description="Total number of log records ingested into storage",
        unit="logs",
    )

    metrics_ingested_counter = meter.create_counter(
        name="storage.metrics.ingested",
        description="Total number of metric data points ingested into storage",
        unit="datapoints",
    )

    # Histogram for ingestion batch sizes
    ingestion_batch_size_histogram = meter.create_histogram(
        name="storage.ingestion.batch_size",
        description="Distribution of ingestion batch sizes",
        unit="items",
    )

    # ============================================================================
    # QUERY METRICS
    # ============================================================================

    query_latency_histogram = meter.create_histogram(
        name="storage.query.duration",
        description="Query operation latency",
        unit="ms",
    )

    # ============================================================================
    # DIMENSION CACHE METRICS
    # ============================================================================

    dimension_cache_ops_counter = meter.create_counter(
        name="storage.dimension_cache.operations",
        description="Count of dimension cache operations (hits/misses)",
        unit="operations",
    )

    dimension_upserts_counter = meter.create_counter(
        name="storage.dimension.upserts",
        description="Count of dimension upserts by dimension type",
        unit="operations",
    )

    # ============================================================================
    # CONNECTION POOL METRICS
    # ============================================================================

    connection_pool_size_gauge = meter.create_up_down_counter(
        name="storage.connection_pool.size",
        description="Current size of database connection pool by state",
        unit="connections",
    )

    # ============================================================================
    # ERROR METRICS
    # ============================================================================

    storage_errors_counter = meter.create_counter(
        name="storage.errors",
        description="Count of storage operation errors by operation type",
        unit="errors",
    )


# Initialize metrics at module load
_create_metrics()


# ============================================================================
# METRIC RECORDING HELPERS
# ============================================================================


def record_spans_ingested(count: int, attributes: dict[str, Any] | None = None) -> None:
    """Record spans ingested into storage.

    Args:
        count: Number of spans ingested
        attributes: Optional attributes (tenant_id, service_name, etc.)
    """
    spans_ingested_counter.add(count, attributes or {})


def record_logs_ingested(count: int, attributes: dict[str, Any] | None = None) -> None:
    """Record log records ingested into storage.

    Args:
        count: Number of log records ingested
        attributes: Optional attributes (tenant_id, service_name, etc.)
    """
    logs_ingested_counter.add(count, attributes or {})


def record_metrics_ingested(count: int, attributes: dict[str, Any] | None = None) -> None:
    """Record metric data points ingested into storage.

    Args:
        count: Number of metric data points ingested
        attributes: Optional attributes (tenant_id, metric_name, etc.)
    """
    metrics_ingested_counter.add(count, attributes or {})


def record_ingestion_batch_size(size: int, signal_type: str) -> None:
    """Record the size of an ingestion batch.

    Args:
        size: Number of items in batch
        signal_type: Type of signal (traces, logs, metrics)
    """
    ingestion_batch_size_histogram.record(size, {"signal_type": signal_type})


def record_query_latency(duration_ms: float, operation: str, attributes: dict[str, Any] | None = None) -> None:
    """Record query operation latency.

    Args:
        duration_ms: Query duration in milliseconds
        operation: Operation name (search_traces, get_trace_by_id, etc.)
        attributes: Optional attributes (tenant_id, result_count, etc.)
    """
    attrs = {"operation": operation}
    if attributes:
        attrs.update(attributes)
    query_latency_histogram.record(duration_ms, attrs)


def record_dimension_cache_operation(dimension_type: str, hit: bool, attributes: dict[str, Any] | None = None) -> None:
    """Record dimension cache hit or miss.

    Args:
        dimension_type: Type of dimension (namespace, service, operation, resource)
        hit: True if cache hit, False if cache miss
        attributes: Optional additional attributes
    """
    attrs = {"dimension_type": dimension_type, "result": "hit" if hit else "miss"}
    if attributes:
        attrs.update(attributes)
    dimension_cache_ops_counter.add(1, attrs)


def record_dimension_upsert(dimension_type: str, created: bool, attributes: dict[str, Any] | None = None) -> None:
    """Record dimension upsert operation.

    Args:
        dimension_type: Type of dimension (namespace, service, operation, resource)
        created: True if new dimension created, False if existing found
        attributes: Optional additional attributes
    """
    attrs = {"dimension_type": dimension_type, "created": created}
    if attributes:
        attrs.update(attributes)
    dimension_upserts_counter.add(1, attrs)


def record_connection_pool_state(active: int, idle: int, waiting: int = 0) -> None:
    """Record connection pool state.

    Args:
        active: Number of active connections
        idle: Number of idle connections
        waiting: Number of threads waiting for connections
    """
    connection_pool_size_gauge.add(active, {"state": "active"})
    connection_pool_size_gauge.add(idle, {"state": "idle"})
    if waiting > 0:
        connection_pool_size_gauge.add(waiting, {"state": "waiting"})


def record_storage_error(operation: str, error_type: str, attributes: dict[str, Any] | None = None) -> None:
    """Record storage operation error.

    Args:
        operation: Operation that failed (store_traces, store_logs, search_traces, etc.)
        error_type: Type of error (DatabaseError, ValidationError, etc.)
        attributes: Optional attributes (tenant_id, etc.)
    """
    attrs = {"operation": operation, "error_type": error_type}
    if attributes:
        attrs.update(attributes)
    storage_errors_counter.add(1, attrs)


# ============================================================================
# PARTITION HEALTH CALLBACKS
# ============================================================================


def register_partition_health_callbacks(callback_func: Any) -> None:
    """Register callback function for partition health metrics.

    Args:
        callback_func: Function that returns partition health stats
            Should return dict with keys: partition_count, total_size_bytes, oldest_partition_age_days
    """
    global partition_count_gauge, partition_size_gauge, oldest_partition_age_gauge

    def partition_count_callback(_) -> None:
        """Callback to report partition count."""
        try:
            stats = callback_func()
            return [(stats.get("partition_count", 0), {})]
        except Exception as e:
            logger.error("Error in partition count callback: %s", e)
            return [(0, {})]

    def partition_size_callback(_) -> None:
        """Callback to report total partition size in bytes."""
        try:
            stats = callback_func()
            return [(stats.get("total_size_bytes", 0), {})]
        except Exception as e:
            logger.error("Error in partition size callback: %s", e)
            return [(0, {})]

    def oldest_partition_age_callback(_) -> None:
        """Callback to report oldest partition age in days."""
        try:
            stats = callback_func()
            return [(stats.get("oldest_partition_age_days", 0), {})]
        except Exception as e:
            logger.error("Error in oldest partition age callback: %s", e)
            return [(0, {})]

    partition_count_gauge = meter.create_observable_gauge(
        name="storage.partitions.count",
        description="Number of active partitions in storage",
        unit="partitions",
        callbacks=[partition_count_callback],
    )

    partition_size_gauge = meter.create_observable_gauge(
        name="storage.partitions.size_bytes",
        description="Total size of all partitions in bytes",
        unit="bytes",
        callbacks=[partition_size_callback],
    )

    oldest_partition_age_gauge = meter.create_observable_gauge(
        name="storage.partitions.oldest_age_days",
        description="Age of oldest partition in days",
        unit="days",
        callbacks=[oldest_partition_age_callback],
    )
