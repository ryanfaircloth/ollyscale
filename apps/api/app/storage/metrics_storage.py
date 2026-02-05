"""
Metrics Storage Implementation

Handles OTLP metrics record ingestion using the new schema:
- Resource/scope dimension management via ResourceManager
- Attribute promotion/storage via AttributeManager
- Metric dimension table (otel_metrics_dim) for metadata deduplication
- Four data point tables:
  * otel_metrics_data_points_number (Gauge, Sum)
  * otel_metrics_data_points_histogram
  * otel_metrics_data_points_exp_histogram
  * otel_metrics_data_points_summary
- Integration with AttributePromotionConfig for promotion rules
"""

import hashlib
import json
import logging
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.storage.attribute_manager import AttributeManager
from app.storage.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class MetricsStorage:
    """
    Manages OTLP metrics record storage with new schema.

    Uses DRY managers (ResourceManager, AttributeManager) for dimension
    and attribute handling. Supports all OTLP metric types with separate
    data point tables for optimal query performance.
    """

    def __init__(self, session: Session):
        """
        Initialize MetricsStorage.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.resource_manager = ResourceManager(session)
        self.attribute_manager = AttributeManager(session)

        # Metric dimension cache (metric_hash -> metric_id)
        self._metric_cache: dict[str, int] = {}

    def _flatten_otlp_attributes(self, otlp_attrs: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Convert OTLP KeyValue list to flat dict.

        OTLP format: [{"key": "http.method", "value": {"stringValue": "GET"}}]
        Flat format: {"http.method": "GET"}

        Args:
            otlp_attrs: List of OTLP KeyValue dicts

        Returns:
            Flattened attribute dict (key -> simple value)
        """
        flattened = {}
        for kv in otlp_attrs:
            key = kv.get("key")
            value_struct = kv.get("value", {})

            # Extract simple value from AnyValue
            if "stringValue" in value_struct:
                flattened[key] = value_struct["stringValue"]
            elif "intValue" in value_struct:
                int_val = value_struct["intValue"]
                flattened[key] = int(int_val) if isinstance(int_val, str) else int_val
            elif "doubleValue" in value_struct:
                flattened[key] = float(value_struct["doubleValue"])
            elif "boolValue" in value_struct:
                flattened[key] = bool(value_struct["boolValue"])
            elif "bytesValue" in value_struct:
                flattened[key] = value_struct["bytesValue"]
            else:
                # Complex type - store as-is
                flattened[key] = value_struct

        return flattened

    def _compute_metric_hash(
        self,
        name: str,
        metric_type: str,
        unit: str,
        description: str,
        is_monotonic: bool | None,
        aggregation_temporality: str | None,
    ) -> tuple[str, str]:
        """
        Compute metric hashes for deduplication.

        Returns two hashes:
        1. metric_hash: Includes description (unique per variant)
        2. metric_identity_hash: Excludes description (groups variants)

        Args:
            name: Metric name
            metric_type: Metric type (Gauge, Sum, Histogram, etc.)
            unit: Unit string
            description: Metric description
            is_monotonic: For Sum metrics, whether monotonic
            aggregation_temporality: Delta or Cumulative

        Returns:
            (metric_hash, metric_identity_hash) tuple
        """
        # Identity components (no description)
        identity_parts = [
            name,
            metric_type,
            unit or "",
            str(is_monotonic) if is_monotonic is not None else "",
            aggregation_temporality or "",
        ]
        identity_str = "|".join(identity_parts)
        identity_hash = hashlib.sha256(identity_str.encode()).hexdigest()

        # Full hash includes description
        full_parts = [*identity_parts, description or ""]
        full_str = "|".join(full_parts)
        metric_hash = hashlib.sha256(full_str.encode()).hexdigest()

        return metric_hash, identity_hash

    def _get_or_create_metric_dimension(
        self,
        name: str,
        metric_type_id: int,
        unit: str | None,
        description: str | None,
        is_monotonic: bool | None,
        aggregation_temporality_id: int | None,
        schema_url: str | None,
    ) -> tuple[int, bool]:
        """
        Get or create metric dimension record.

        Uses two-hash strategy for description variant support.

        Args:
            name: Metric name
            metric_type_id: Metric type ID from metric_types enum table
            unit: Unit string
            description: Metric description
            is_monotonic: For Sum metrics
            aggregation_temporality_id: Temporality ID from enum table
            schema_url: Schema URL

        Returns:
            (metric_id, created) tuple
        """
        # Map type ID to type string for hashing (simplified)
        # In real implementation, would query metric_types table
        type_map = {1: "Gauge", 2: "Sum", 3: "Histogram", 4: "ExponentialHistogram", 5: "Summary"}
        metric_type = type_map.get(metric_type_id, "Unknown")

        # Map temporality ID to string
        temp_map = {1: "Delta", 2: "Cumulative"}
        temporality = temp_map.get(aggregation_temporality_id) if aggregation_temporality_id else None

        metric_hash, identity_hash = self._compute_metric_hash(
            name, metric_type, unit or "", description or "", is_monotonic, temporality
        )

        # Check cache
        if metric_hash in self._metric_cache:
            return self._metric_cache[metric_hash], False

        # Check database
        result = self.session.execute(
            text(
                """
                SELECT metric_id FROM otel_metrics_dim
                WHERE metric_hash = :metric_hash
                """
            ),
            {"metric_hash": metric_hash},
        )
        row = result.fetchone()

        if row:
            metric_id = row[0]
            self._metric_cache[metric_hash] = metric_id
            return metric_id, False

        # Create new metric dimension
        self.session.execute(
            text(
                """
                INSERT INTO otel_metrics_dim (
                    metric_hash, metric_identity_hash, name, metric_type_id,
                    unit, aggregation_temporality_id, is_monotonic, description, schema_url
                )
                VALUES (
                    :metric_hash, :identity_hash, :name, :metric_type_id,
                    :unit, :aggregation_temporality_id, :is_monotonic, :description, :schema_url
                )
                RETURNING metric_id
                """
            ),
            {
                "metric_hash": metric_hash,
                "identity_hash": identity_hash,
                "name": name,
                "metric_type_id": metric_type_id,
                "unit": unit,
                "aggregation_temporality_id": aggregation_temporality_id,
                "is_monotonic": is_monotonic,
                "description": description,
                "schema_url": schema_url,
            },
        )
        result = self.session.execute(text("SELECT lastval()"))
        metric_id = result.scalar()

        self._metric_cache[metric_hash] = metric_id
        return metric_id, True

    def store_metrics(self, resource_metrics: dict[str, Any]) -> dict[str, Any]:
        """
        Store OTLP metrics from a single ResourceMetrics entry.

        Args:
            resource_metrics: Single OTLP ResourceMetrics dict with structure:
                {
                    "resource": {"attributes": [...]},
                    "scopeMetrics": [{
                        "scope": {"name": "...", "version": "..."},
                        "metrics": [{
                            "name": "...",
                            "gauge": {"dataPoints": [...]},  # OR
                            "sum": {"dataPoints": [...], "aggregationTemporality": ..., "isMonotonic": ...},  # OR
                            "histogram": {"dataPoints": [...], "aggregationTemporality": ...},  # etc
                        }]
                    }]
                }

        Returns:
            Storage statistics
        """
        stats = {
            "data_points_stored": 0,
            "resources_created": 0,
            "scopes_created": 0,
            "metrics_created": 0,
            "attributes_promoted": 0,
            "attributes_other": 0,
        }

        # Handle resource dimension
        resource_attrs_otlp = resource_metrics.get("resource", {}).get("attributes", [])
        resource_attrs_flat = self._flatten_otlp_attributes(resource_attrs_otlp)

        resource_id, created, _ = self.resource_manager.get_or_create_resource(resource_attrs_flat)
        if created:
            stats["resources_created"] += 1

        # Process scope metrics
        scope_metrics_list = resource_metrics.get("scopeMetrics", [])

        for scope_metrics in scope_metrics_list:
            # Handle scope dimension
            scope_info = scope_metrics.get("scope", {})
            scope_name = scope_info.get("name", "")
            scope_version = scope_info.get("version", "")
            scope_attrs_otlp = scope_info.get("attributes", [])
            scope_attrs_flat = self._flatten_otlp_attributes(scope_attrs_otlp)

            scope_id, created, _ = self.resource_manager.get_or_create_scope(
                scope_name, scope_version, scope_attrs_flat
            )
            if created:
                stats["scopes_created"] += 1

            # Process metrics
            metrics = scope_metrics.get("metrics", [])

            for metric in metrics:
                self._store_metric(metric, resource_id, scope_id, stats)

        return stats

    def _store_metric(
        self,
        metric: dict[str, Any],
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """
        Store a single metric with all its data points.

        Args:
            metric: OTLP Metric dict
            resource_id: Resource dimension ID
            scope_id: Scope dimension ID
            stats: Statistics dict to update
        """
        name = metric.get("name", "")
        description = metric.get("description", "")
        unit = metric.get("unit", "")

        # Determine metric type and extract data points
        if "gauge" in metric:
            self._store_gauge(metric["gauge"], name, description, unit, resource_id, scope_id, stats)
        elif "sum" in metric:
            self._store_sum(metric["sum"], name, description, unit, resource_id, scope_id, stats)
        elif "histogram" in metric:
            self._store_histogram(metric["histogram"], name, description, unit, resource_id, scope_id, stats)
        elif "exponentialHistogram" in metric:
            self._store_exp_histogram(
                metric["exponentialHistogram"], name, description, unit, resource_id, scope_id, stats
            )
        elif "summary" in metric:
            self._store_summary(metric["summary"], name, description, unit, resource_id, scope_id, stats)
        else:
            logger.warning(f"Unknown metric type for metric: {name}")

    def _store_gauge(
        self,
        gauge: dict[str, Any],
        name: str,
        description: str,
        unit: str,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """Store Gauge metric data points."""
        metric_type_id = 1  # Gauge
        metric_id, created = self._get_or_create_metric_dimension(
            name, metric_type_id, unit, description, None, None, None
        )
        if created:
            stats["metrics_created"] += 1

        data_points = gauge.get("dataPoints", [])
        for dp in data_points:
            self._store_number_data_point(dp, metric_id, resource_id, scope_id, stats)

    def _store_sum(
        self,
        sum_metric: dict[str, Any],
        name: str,
        description: str,
        unit: str,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """Store Sum metric data points."""
        metric_type_id = 2  # Sum
        is_monotonic = sum_metric.get("isMonotonic", False)
        aggregation_temporality = sum_metric.get("aggregationTemporality", 0)

        # Map OTLP temporality enum to DB ID (0=unspecified, 1=delta, 2=cumulative)
        temporality_id = aggregation_temporality if aggregation_temporality in (1, 2) else None

        metric_id, created = self._get_or_create_metric_dimension(
            name, metric_type_id, unit, description, is_monotonic, temporality_id, None
        )
        if created:
            stats["metrics_created"] += 1

        data_points = sum_metric.get("dataPoints", [])
        for dp in data_points:
            self._store_number_data_point(dp, metric_id, resource_id, scope_id, stats)

    def _store_number_data_point(
        self,
        dp: dict[str, Any],
        metric_id: int,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """
        Store a number (Gauge/Sum) data point.

        Args:
            dp: OTLP NumberDataPoint dict
            metric_id: Metric dimension ID
            resource_id: Resource ID
            scope_id: Scope ID
            stats: Statistics dict

        Returns:
            data_point_id: Primary key of inserted data point
        """
        start_time_unix_nano = int(dp.get("startTimeUnixNano", 0)) if "startTimeUnixNano" in dp else None
        time_unix_nano = int(dp.get("timeUnixNano", 0))
        flags = int(dp.get("flags", 0))

        # Extract value (int or double)
        value_int = None
        value_double = None
        if "asInt" in dp:
            int_val = dp["asInt"]
            value_int = int(int_val) if isinstance(int_val, str) else int_val
        elif "asDouble" in dp:
            value_double = float(dp["asDouble"])

        # Handle exemplars as JSONB
        exemplars = dp.get("exemplars", [])
        exemplars_json = json.dumps(exemplars) if exemplars else None

        # Handle attributes
        dp_attrs_otlp = dp.get("attributes", [])
        dp_attrs_anyvalue = {}
        for kv in dp_attrs_otlp:
            key = kv.get("key")
            value = kv.get("value", {})
            dp_attrs_anyvalue[key] = value

        # Determine attributes_other JSONB
        # For Phase 4, we'll store ALL attributes in attributes_other for simplicity
        # In future, we can promote selected attributes to typed tables
        attributes_other_json = json.dumps(self._flatten_otlp_attributes(dp_attrs_otlp)) if dp_attrs_otlp else None

        # Insert data point
        self.session.execute(
            text(
                """
                INSERT INTO otel_metrics_data_points_number (
                    metric_id, resource_id, scope_id, start_time_unix_nano, time_unix_nano,
                    value_int, value_double, flags, exemplars, attributes_other
                )
                VALUES (
                    :metric_id, :resource_id, :scope_id, :start_time_unix_nano, :time_unix_nano,
                    :value_int, :value_double, :flags, :exemplars, :attributes_other
                )
                RETURNING data_point_id
                """
            ),
            {
                "metric_id": metric_id,
                "resource_id": resource_id,
                "scope_id": scope_id,
                "start_time_unix_nano": start_time_unix_nano,
                "time_unix_nano": time_unix_nano,
                "value_int": value_int,
                "value_double": value_double,
                "flags": flags,
                "exemplars": exemplars_json,
                "attributes_other": attributes_other_json,
            },
        )

        result = self.session.execute(text("SELECT lastval()"))
        data_point_id = result.scalar()

        stats["data_points_stored"] += 1
        if attributes_other_json:
            stats["attributes_other"] += len(dp_attrs_otlp)

        return data_point_id

    def _store_histogram(
        self,
        histogram: dict[str, Any],
        name: str,
        description: str,
        unit: str,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """Store Histogram metric data points."""
        metric_type_id = 3  # Histogram
        aggregation_temporality = histogram.get("aggregationTemporality", 0)
        temporality_id = aggregation_temporality if aggregation_temporality in (1, 2) else None

        metric_id, created = self._get_or_create_metric_dimension(
            name, metric_type_id, unit, description, None, temporality_id, None
        )
        if created:
            stats["metrics_created"] += 1

        data_points = histogram.get("dataPoints", [])
        for dp in data_points:
            self._store_histogram_data_point(dp, metric_id, resource_id, scope_id, stats)

    def _store_histogram_data_point(
        self,
        dp: dict[str, Any],
        metric_id: int,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """Store a histogram data point."""
        start_time_unix_nano = int(dp.get("startTimeUnixNano", 0)) if "startTimeUnixNano" in dp else None
        time_unix_nano = int(dp.get("timeUnixNano", 0))
        count = int(dp.get("count", 0))
        sum_val = float(dp.get("sum")) if "sum" in dp else None
        min_val = float(dp.get("min")) if "min" in dp else None
        max_val = float(dp.get("max")) if "max" in dp else None
        flags = int(dp.get("flags", 0))

        # Buckets
        explicit_bounds = dp.get("explicitBounds", [])
        bucket_counts = dp.get("bucketCounts", [])
        exemplars = dp.get("exemplars", [])
        exemplars_json = json.dumps(exemplars) if exemplars else None

        # Attributes
        dp_attrs_otlp = dp.get("attributes", [])
        attributes_other_json = json.dumps(self._flatten_otlp_attributes(dp_attrs_otlp)) if dp_attrs_otlp else None

        # Convert Python lists to PostgreSQL arrays notation
        bounds_str = "{" + ",".join(map(str, explicit_bounds)) + "}" if explicit_bounds else None
        counts_str = "{" + ",".join(map(str, bucket_counts)) + "}" if bucket_counts else None

        self.session.execute(
            text(
                """
                INSERT INTO otel_metrics_data_points_histogram (
                    metric_id, resource_id, scope_id, start_time_unix_nano, time_unix_nano,
                    count, sum, min, max, explicit_bounds, bucket_counts, flags, exemplars, attributes_other
                )
                VALUES (
                    :metric_id, :resource_id, :scope_id, :start_time_unix_nano, :time_unix_nano,
                    :count, :sum, :min, :max, :explicit_bounds::double precision[], :bucket_counts::bigint[], :flags, :exemplars, :attributes_other
                )
                RETURNING data_point_id
                """
            ),
            {
                "metric_id": metric_id,
                "resource_id": resource_id,
                "scope_id": scope_id,
                "start_time_unix_nano": start_time_unix_nano,
                "time_unix_nano": time_unix_nano,
                "count": count,
                "sum": sum_val,
                "min": min_val,
                "max": max_val,
                "explicit_bounds": bounds_str,
                "bucket_counts": counts_str,
                "flags": flags,
                "exemplars": exemplars_json,
                "attributes_other": attributes_other_json,
            },
        )

        result = self.session.execute(text("SELECT lastval()"))
        data_point_id = result.scalar()

        stats["data_points_stored"] += 1
        if attributes_other_json:
            stats["attributes_other"] += len(dp_attrs_otlp)

        return data_point_id

    def _store_exp_histogram(
        self,
        exp_histogram: dict[str, Any],
        name: str,
        description: str,
        unit: str,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """Store ExponentialHistogram metric data points."""
        metric_type_id = 4  # ExponentialHistogram
        aggregation_temporality = exp_histogram.get("aggregationTemporality", 0)
        temporality_id = aggregation_temporality if aggregation_temporality in (1, 2) else None

        metric_id, created = self._get_or_create_metric_dimension(
            name, metric_type_id, unit, description, None, temporality_id, None
        )
        if created:
            stats["metrics_created"] += 1

        data_points = exp_histogram.get("dataPoints", [])
        for dp in data_points:
            self._store_exp_histogram_data_point(dp, metric_id, resource_id, scope_id, stats)

    def _store_exp_histogram_data_point(
        self,
        dp: dict[str, Any],
        metric_id: int,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """Store an exponential histogram data point."""
        start_time_unix_nano = int(dp.get("startTimeUnixNano", 0)) if "startTimeUnixNano" in dp else None
        time_unix_nano = int(dp.get("timeUnixNano", 0))
        count = int(dp.get("count", 0))
        sum_val = float(dp.get("sum")) if "sum" in dp else None
        min_val = float(dp.get("min")) if "min" in dp else None
        max_val = float(dp.get("max")) if "max" in dp else None
        scale = int(dp.get("scale", 0))
        zero_count = int(dp.get("zeroCount", 0))
        flags = int(dp.get("flags", 0))

        # Positive buckets
        positive = dp.get("positive", {})
        positive_offset = int(positive.get("offset", 0)) if positive else None
        positive_bucket_counts = positive.get("bucketCounts", []) if positive else []

        # Negative buckets
        negative = dp.get("negative", {})
        negative_offset = int(negative.get("offset", 0)) if negative else None
        negative_bucket_counts = negative.get("bucketCounts", []) if negative else []

        exemplars = dp.get("exemplars", [])
        exemplars_json = json.dumps(exemplars) if exemplars else None

        # Attributes
        dp_attrs_otlp = dp.get("attributes", [])
        attributes_other_json = json.dumps(self._flatten_otlp_attributes(dp_attrs_otlp)) if dp_attrs_otlp else None

        # Convert bucket counts to PostgreSQL arrays
        pos_counts_str = "{" + ",".join(map(str, positive_bucket_counts)) + "}" if positive_bucket_counts else None
        neg_counts_str = "{" + ",".join(map(str, negative_bucket_counts)) + "}" if negative_bucket_counts else None

        self.session.execute(
            text(
                """
                INSERT INTO otel_metrics_data_points_exp_histogram (
                    metric_id, resource_id, scope_id, start_time_unix_nano, time_unix_nano,
                    count, sum, min, max, scale, zero_count,
                    positive_offset, positive_bucket_counts,
                    negative_offset, negative_bucket_counts,
                    flags, exemplars, attributes_other
                )
                VALUES (
                    :metric_id, :resource_id, :scope_id, :start_time_unix_nano, :time_unix_nano,
                    :count, :sum, :min, :max, :scale, :zero_count,
                    :positive_offset, :positive_bucket_counts::bigint[],
                    :negative_offset, :negative_bucket_counts::bigint[],
                    :flags, :exemplars, :attributes_other
                )
                RETURNING data_point_id
                """
            ),
            {
                "metric_id": metric_id,
                "resource_id": resource_id,
                "scope_id": scope_id,
                "start_time_unix_nano": start_time_unix_nano,
                "time_unix_nano": time_unix_nano,
                "count": count,
                "sum": sum_val,
                "min": min_val,
                "max": max_val,
                "scale": scale,
                "zero_count": zero_count,
                "positive_offset": positive_offset,
                "positive_bucket_counts": pos_counts_str,
                "negative_offset": negative_offset,
                "negative_bucket_counts": neg_counts_str,
                "flags": flags,
                "exemplars": exemplars_json,
                "attributes_other": attributes_other_json,
            },
        )

        result = self.session.execute(text("SELECT lastval()"))
        data_point_id = result.scalar()

        stats["data_points_stored"] += 1
        if attributes_other_json:
            stats["attributes_other"] += len(dp_attrs_otlp)

        return data_point_id

    def _store_summary(
        self,
        summary: dict[str, Any],
        name: str,
        description: str,
        unit: str,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> None:
        """Store Summary metric data points."""
        metric_type_id = 5  # Summary
        metric_id, created = self._get_or_create_metric_dimension(
            name, metric_type_id, unit, description, None, None, None
        )
        if created:
            stats["metrics_created"] += 1

        data_points = summary.get("dataPoints", [])
        for dp in data_points:
            self._store_summary_data_point(dp, metric_id, resource_id, scope_id, stats)

    def _store_summary_data_point(
        self,
        dp: dict[str, Any],
        metric_id: int,
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """Store a summary data point."""
        start_time_unix_nano = int(dp.get("startTimeUnixNano", 0)) if "startTimeUnixNano" in dp else None
        time_unix_nano = int(dp.get("timeUnixNano", 0))
        count = int(dp.get("count", 0))
        sum_val = float(dp.get("sum", 0))
        flags = int(dp.get("flags", 0))

        # Quantile values
        quantile_values = dp.get("quantileValues", [])
        quantile_json = json.dumps(quantile_values) if quantile_values else None

        # Attributes
        dp_attrs_otlp = dp.get("attributes", [])
        attributes_other_json = json.dumps(self._flatten_otlp_attributes(dp_attrs_otlp)) if dp_attrs_otlp else None

        self.session.execute(
            text(
                """
                INSERT INTO otel_metrics_data_points_summary (
                    metric_id, resource_id, scope_id, start_time_unix_nano, time_unix_nano,
                    count, sum, quantile_values, flags, attributes_other
                )
                VALUES (
                    :metric_id, :resource_id, :scope_id, :start_time_unix_nano, :time_unix_nano,
                    :count, :sum, :quantile_values, :flags, :attributes_other
                )
                RETURNING data_point_id
                """
            ),
            {
                "metric_id": metric_id,
                "resource_id": resource_id,
                "scope_id": scope_id,
                "start_time_unix_nano": start_time_unix_nano,
                "time_unix_nano": time_unix_nano,
                "count": count,
                "sum": sum_val,
                "quantile_values": quantile_json,
                "flags": flags,
                "attributes_other": attributes_other_json,
            },
        )

        result = self.session.execute(text("SELECT lastval()"))
        data_point_id = result.scalar()

        stats["data_points_stored"] += 1
        if attributes_other_json:
            stats["attributes_other"] += len(dp_attrs_otlp)

        return data_point_id

    def get_metrics(
        self,
        start_time: int,
        end_time: int,
        metric_name: str | None = None,
        limit: int = 1000,
    ) -> list[tuple]:
        """
        Query metrics data points (simplified query across all types).

        Args:
            start_time: Start time in nanoseconds
            end_time: End time in nanoseconds
            metric_name: Optional metric name filter
            limit: Maximum number of data points to return

        Returns:
            List of data point tuples
        """
        base_query = """
            SELECT
                m.name, m.metric_type_id, m.unit,
                dp.time_unix_nano, dp.value_int, dp.value_double,
                dp.resource_id, dp.scope_id
            FROM otel_metrics_data_points_number dp
            JOIN otel_metrics_dim m ON dp.metric_id = m.metric_id
            WHERE dp.time_unix_nano BETWEEN :start_time AND :end_time
        """

        if metric_name:
            base_query += " AND m.name = :metric_name"

        base_query += " ORDER BY dp.time_unix_nano DESC LIMIT :limit"

        params = {"start_time": start_time, "end_time": end_time, "limit": limit}
        if metric_name:
            params["metric_name"] = metric_name

        result = self.session.execute(text(base_query), params)
        return result.fetchall()
