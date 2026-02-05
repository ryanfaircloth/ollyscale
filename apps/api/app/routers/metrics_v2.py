"""v2 metrics query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
MetricsStorage and v_otel_metrics_enriched view. They coexist with v1 endpoints
until Phase 5 migration.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import text
from sqlmodel import Session

from app.dependencies import get_db_session
from app.storage.metrics_storage import MetricsStorage

router = APIRouter(prefix="/v2/metrics", tags=["metrics-v2"])
logger = logging.getLogger(__name__)


def get_metrics_storage(session: Annotated[Session, Depends(get_db_session)]) -> MetricsStorage:
    """Dependency to get MetricsStorage instance."""
    return MetricsStorage(session)


@router.get("/search")
def search_metrics_v2(
    metric_name: Annotated[str, Query(description="Metric name to query")],
    start_time: Annotated[int, Query(description="Start time in nanoseconds since Unix epoch")],
    end_time: Annotated[int, Query(description="End time in nanoseconds since Unix epoch")],
    service_name: Annotated[str | None, Query(description="Filter by service name")] = None,
    limit: Annotated[int, Query(description="Maximum number of data points", ge=1, le=10000)] = 1000,
    metrics_storage: Annotated[MetricsStorage, Depends(get_metrics_storage)] = None,
):
    """Search metric time series with filters using v2 OTLP schema.

    Returns metric data points with enriched resource and scope context.
    Uses v_otel_metrics_enriched view for unified queries across all metric types.

    Query parameters:
    - metric_name: Name of the metric to query (required)
    - start_time, end_time: Time range in nanoseconds (required)
    - service_name: Filter by service name (optional)
    - limit: Max data points (default 1000, max 10000)

    Response includes:
    - metric_name, unit, metric_type
    - data_points: Array of time series points with values and attributes
    - resource_context: Service name/namespace
    - scope_context: Instrumentation library info
    - aggregation_temporality: Delta or Cumulative
    """
    try:
        # Build query using v_otel_metrics_enriched view
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
            WHERE metric_name = :metric_name
              AND time BETWEEN :start_time AND :end_time
              AND (:service_name IS NULL OR service_name = :service_name)
            ORDER BY time DESC
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

        # Convert rows to structured response
        data_points = []
        for row in rows:
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

            data_points.append(point)

        # Get first row for metadata (all data points share same metric metadata)
        if rows:
            first = rows[0]
            return {
                "metric_name": metric_name,
                "metric_type": first.metric_type,
                "unit": first.unit,
                "aggregation_temporality": first.aggregation_temporality,
                "resource": {
                    "service_name": first.service_name,
                    "service_namespace": first.service_namespace,
                },
                "scope": {
                    "name": first.scope_name,
                    "version": first.scope_version,
                },
                "data_points": data_points,
                "count": len(data_points),
                "limit": limit,
                "has_more": len(data_points) == limit,
            }
        else:
            return {
                "metric_name": metric_name,
                "data_points": [],
                "count": 0,
                "limit": limit,
                "has_more": False,
            }

    except Exception as e:
        logger.exception("Failed to search metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search metrics: {str(e)}",
        )


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
            detail=f"Failed to get metric labels: {str(e)}",
        )
