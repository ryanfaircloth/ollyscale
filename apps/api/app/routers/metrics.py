"""Metrics query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
MetricsStorage and v_otel_metrics_enriched view.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import text
from sqlmodel import Session

from app.dependencies import get_db_session
from app.models.api import Metric, MetricSearchRequest, MetricSearchResponse, PaginationResponse
from app.storage.metrics_storage import MetricsStorage

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


def get_metrics_storage(session: Annotated[Session, Depends(get_db_session)]) -> MetricsStorage:
    """Dependency to get MetricsStorage instance."""
    return MetricsStorage(session)


def rfc3339_to_nanoseconds(rfc3339_str: str) -> int:
    """Convert RFC3339 timestamp to Unix nanoseconds."""
    dt = datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1_000_000_000)


@router.post("/search", response_model=MetricSearchResponse)
def search_metrics(
    request: MetricSearchRequest,
    metrics_storage: Annotated[MetricsStorage, Depends(get_metrics_storage)],
):
    """Search metric time series with filters using OTLP schema.

    Request body includes:
    - time_range: Start/end times in RFC3339 format
    - metric_names: Optional list of metric names to query
    - filters: Optional filters (service.name)
    - pagination: Limit and cursor

    Response includes:
    - metrics: Array of metric objects with data points
    - pagination: Has_more flag and next cursor
    """
    try:
        # Convert RFC3339 to nanoseconds
        start_time = rfc3339_to_nanoseconds(request.time_range.start_time)
        end_time = rfc3339_to_nanoseconds(request.time_range.end_time)

        # Extract metric_names from request
        metric_name = request.metric_names[0] if request.metric_names and len(request.metric_names) > 0 else None

        # Extract service_name from filters
        service_name = None
        if request.filters:
            for f in request.filters:
                if f.field == "service.name" and f.operator == "eq":
                    service_name = str(f.value)

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
                "limit": request.pagination.limit,
            },
        )

        rows = result.fetchall()

        # Group rows by metric_name
        metrics_dict = defaultdict(lambda: {"data_points": [], "metadata": None})

        for row in rows:
            metric_key = row.metric_name

            # Build data point
            point = {
                "time_unix_nano": int(row.time.timestamp() * 1_000_000_000) if row.time else None,
                "value": row.value
                if row.value is not None
                else row.sum
                if row.sum is not None
                else row.count
                if row.count is not None
                else 0,
                "attributes": [{"key": k, "value": v} for k, v in (row.attributes_other or {}).items()],
            }

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

        # Build response as list of Metric objects
        metrics_list = []
        for metric_key, metric_data in metrics_dict.items():
            metadata = metric_data["metadata"]
            metrics_list.append(
                Metric(
                    name=metric_key,
                    metric_type=metadata["metric_type"],
                    unit=metadata["unit"],
                    aggregation_temporality=metadata["aggregation_temporality"],
                    service_name=metadata["service_name"],
                    service_namespace=metadata["service_namespace"],
                    data_points=metric_data["data_points"],
                    resource={
                        "service_name": metadata["service_name"],
                        "service_namespace": metadata["service_namespace"],
                    },
                    scope={"name": metadata["scope_name"], "version": metadata["scope_version"]},
                )
            )

        return MetricSearchResponse(
            metrics=metrics_list,
            pagination=PaginationResponse(
                has_more=len(rows) == request.pagination.limit,
                next_cursor=None,
                total_count=None,
            ),
        )

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
