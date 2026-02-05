"""v2 metrics query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
MetricsStorage and v_otel_metrics_enriched view. They coexist with v1 endpoints
until Phase 5 migration.
"""

import logging
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import text
from sqlmodel import Session

from app.dependencies import get_db_session
from app.storage.metrics_storage import MetricsStorage

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


def get_metrics_storage(session: Annotated[Session, Depends(get_db_session)]) -> MetricsStorage:
    """Dependency to get MetricsStorage instance."""
    return MetricsStorage(session)


@router.get("/search")
def search_metrics_v2(
    start_time: Annotated[int, Query(description="Start time in nanoseconds since Unix epoch")],
    end_time: Annotated[int, Query(description="End time in nanoseconds since Unix epoch")],
    metric_name: Annotated[str | None, Query(description="Filter by metric name")] = None,
    service_name: Annotated[str | None, Query(description="Filter by service name")] = None,
    limit: Annotated[int, Query(description="Maximum number of data points per metric", ge=1, le=10000)] = 1000,
    metrics_storage: Annotated[MetricsStorage, Depends(get_metrics_storage)] = None,
):
    """Search metric time series with filters using v2 OTLP schema.

    Returns metric data points with enriched resource and scope context.
    Uses v_otel_metrics_enriched view for unified queries across all metric types.

    Query parameters:
    - start_time, end_time: Time range in nanoseconds (required)
    - metric_name: Filter by metric name (optional, returns all metrics if not specified)
    - service_name: Filter by service name (optional)
    - limit: Max data points per metric (default 1000, max 10000)

    Response includes:
    - metrics: Array of metric objects, each containing:
      - metric_name, unit, metric_type
      - data_points: Array of time series points with values and attributes
      - resource: Service name/namespace
      - scope: Instrumentation library info
      - aggregation_temporality: Delta or Cumulative
    """
    try:
        # Build query using v_otel_metrics_enriched view
        # Convert nanosecond timestamps to PostgreSQL timestamps
        query = text(
            """
            SELECT
                metric_name,
                metric_type,
                unit,
                aggregation_temporality,
                start_time,
                time,
                value,
                count,
                sum,
                min,
                max,
                explicit_bounds,
                bucket_counts,
                scale,
                zero_count,
                positive_offset,
                positive_bucket_counts,
                negative_offset,
                negative_bucket_counts,
                quantile_values,
                flags,
                exemplars,
                service_name,
                service_namespace,
                scope_name,
                scope_version,
                attributes_other
            FROM v_otel_metrics_enriched
            WHERE time BETWEEN to_timestamp(:start_time / 1000000000.0)
                           AND to_timestamp(:end_time / 1000000000.0)
              AND (:metric_name IS NULL OR metric_name = :metric_name)
              AND (:service_name IS NULL OR service_name = :service_name)
            ORDER BY metric_name, time DESC
            LIMIT :limit
            """
        )

        result = metrics_storage.session.execute(
            query,
            {
                "metric_name": metric_name,
                "start_time": start_time,
                "end_time": end_time,
                "service_name": service_name,
                "limit": limit,
            },
        )

        rows = result.fetchall()

        # Group rows by metric_name
        metrics_dict = defaultdict(lambda: {"data_points": [], "metadata": None})

        for row in rows:
            metric_key = row.metric_name

            # Build data point
            point = {
                "time": row.time,
                "start_time": row.start_time,
                "flags": row.flags,
                "attributes": row.attributes_other,
            }

            # Add type-specific fields (only non-null values)
            if row.value is not None:
                point["value"] = row.value  # Gauge/Sum
            if row.count is not None:
                point["count"] = row.count  # Histogram/ExponentialHistogram/Summary
            if row.sum is not None:
                point["sum"] = row.sum
            if row.min is not None:
                point["min"] = row.min
            if row.max is not None:
                point["max"] = row.max
            if row.explicit_bounds is not None:
                point["explicit_bounds"] = row.explicit_bounds
            if row.bucket_counts is not None:
                point["bucket_counts"] = row.bucket_counts
            if row.scale is not None:
                point["scale"] = row.scale
            if row.zero_count is not None:
                point["zero_count"] = row.zero_count
            if row.positive_offset is not None:
                point["positive_offset"] = row.positive_offset
            if row.positive_bucket_counts is not None:
                point["positive_bucket_counts"] = row.positive_bucket_counts
            if row.negative_offset is not None:
                point["negative_offset"] = row.negative_offset
            if row.negative_bucket_counts is not None:
                point["negative_bucket_counts"] = row.negative_bucket_counts
            if row.quantile_values is not None:
                point["quantile_values"] = row.quantile_values
            if row.exemplars is not None:
                point["exemplars"] = row.exemplars

            metrics_dict[metric_key]["data_points"].append(point)

            # Store metadata from first row of each metric
            if metrics_dict[metric_key]["metadata"] is None:
                metrics_dict[metric_key]["metadata"] = {
                    "metric_type": row.metric_type,
                    "unit": row.unit,
                    "aggregation_temporality": row.aggregation_temporality,
                    "service_name": row.service_name,
                    "service_namespace": row.service_namespace,
                    "scope_name": row.scope_name,
                    "scope_version": row.scope_version,
                }

        # Build response with array of metrics
        metrics = []
        for metric_key, metric_data in metrics_dict.items():
            metadata = metric_data["metadata"]
            metrics.append(
                {
                    "name": metric_key,
                    "type": metadata["metric_type"],
                    "unit": metadata["unit"],
                    "aggregation_temporality": metadata["aggregation_temporality"],
                    "resource": {
                        "service_name": metadata["service_name"],
                        "service_namespace": metadata["service_namespace"],
                    },
                    "scope": {
                        "name": metadata["scope_name"],
                        "version": metadata["scope_version"],
                    },
                    "data_points": metric_data["data_points"],
                }
            )

        return {
            "metrics": metrics,
            "count": len(metrics),
            "total_data_points": sum(len(m["data_points"]) for m in metrics),
            "limit": limit,
            "has_more": len(rows) == limit,
        }

    except Exception as e:
        logger.exception("Failed to search metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search metrics: {e!s}",
        ) from e


@router.get("/{metric_name}/labels")
def get_metric_labels_v2(
    metric_name: Annotated[str, Path(description="Metric name to get labels for")],
    attribute_key: Annotated[str | None, Query(description="Get values for specific attribute key")] = None,
    metrics_storage: Annotated[MetricsStorage, Depends(get_metrics_storage)] = None,
):
    """Get available label keys and values for a metric.

    Returns all distinct attribute keys found in the metric's data points,
    or values for a specific attribute key if provided.

    Path parameters:
    - metric_name: Name of the metric

    Query parameters:
    - attribute_key: Optional specific key to get values for

    Response without attribute_key:
    - metric_name
    - label_keys: Array of distinct attribute keys

    Response with attribute_key:
    - metric_name
    - attribute_key
    - values: Array of distinct values for that key
    """
    try:
        # Get metric_id first
        metric_query = text(
            """
            SELECT metric_id
            FROM otel_metrics_dim
            WHERE name = :metric_name
            LIMIT 1
            """
        )

        result = metrics_storage.session.execute(metric_query, {"metric_name": metric_name})
        metric_row = result.fetchone()

        if not metric_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metric '{metric_name}' not found",
            )

        metric_id = metric_row.metric_id

        if attribute_key:
            # Get distinct values for specific attribute key from all data point tables
            # Use UNION ALL to query all 4 data point tables
            values_query = text(
                """
                SELECT DISTINCT attributes_other->>:attribute_key as value
                FROM (
                    SELECT attributes_other FROM otel_metrics_data_points_number
                    WHERE metric_id = :metric_id AND attributes_other ? :attribute_key
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_histogram
                    WHERE metric_id = :metric_id AND attributes_other ? :attribute_key
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_exp_histogram
                    WHERE metric_id = :metric_id AND attributes_other ? :attribute_key
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_summary
                    WHERE metric_id = :metric_id AND attributes_other ? :attribute_key
                ) all_attrs
                WHERE attributes_other->>:attribute_key IS NOT NULL
                ORDER BY value
                LIMIT 1000
                """
            )

            result = metrics_storage.session.execute(
                values_query,
                {"metric_id": metric_id, "attribute_key": attribute_key},
            )

            values = [row.value for row in result.fetchall()]

            return {
                "metric_name": metric_name,
                "attribute_key": attribute_key,
                "values": values,
                "count": len(values),
            }
        else:
            # Get all distinct attribute keys from all data point tables
            keys_query = text(
                """
                SELECT DISTINCT jsonb_object_keys(attributes_other) as key
                FROM (
                    SELECT attributes_other FROM otel_metrics_data_points_number
                    WHERE metric_id = :metric_id AND attributes_other IS NOT NULL
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_histogram
                    WHERE metric_id = :metric_id AND attributes_other IS NOT NULL
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_exp_histogram
                    WHERE metric_id = :metric_id AND attributes_other IS NOT NULL
                    UNION ALL
                    SELECT attributes_other FROM otel_metrics_data_points_summary
                   WHERE metric_id = :metric_id AND attributes_other IS NOT NULL
                ) all_attrs
                WHERE attributes_other IS NOT NULL
                ORDER BY key
                LIMIT 1000
                """
            )

            result = metrics_storage.session.execute(keys_query, {"metric_id": metric_id})
            keys = [row.key for row in result.fetchall()]

            return {
                "metric_name": metric_name,
                "label_keys": keys,
                "count": len(keys),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get metric labels")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric labels: {e!s}",
        ) from e
