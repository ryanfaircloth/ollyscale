"""Query endpoints for traces, logs, and metrics."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_storage
from app.models.api import (
    LogSearchRequest,
    LogSearchResponse,
    MetricSearchRequest,
    MetricSearchResponse,
    PaginationResponse,
    ServiceListResponse,
    ServiceMapResponse,
    ServiceSearchRequest,
    SpanSearchRequest,
    SpanSearchResponse,
    TraceSearchRequest,
    TraceSearchResponse,
)
from app.storage import StorageBackend

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/traces/search", response_model=TraceSearchResponse)
def search_traces(request: TraceSearchRequest, storage: StorageBackend = Depends(get_storage)):
    """Search traces with filters and pagination."""
    try:
        result = storage.search_traces(
            time_range=request.time_range, filters=request.filters, pagination=request.pagination
        )

        # Handle case where storage returns unexpected format
        if not isinstance(result, tuple) or len(result) != 3:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage returned invalid result format",
            )

        traces, has_more, next_cursor = result

        return TraceSearchResponse(
            traces=traces,
            pagination=PaginationResponse(has_more=has_more, next_cursor=next_cursor, total_count=len(traces)),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search traces: {e!s}",
        ) from e


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str, storage: StorageBackend = Depends(get_storage)):
    """Get trace by ID with all spans."""
    try:
        trace = storage.get_trace_by_id(trace_id)

        if trace is None:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

        return trace
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trace: {e!s}",
        ) from e


@router.post("/spans/search", response_model=SpanSearchResponse)
def search_spans(request: SpanSearchRequest, storage: StorageBackend = Depends(get_storage)):
    """Search spans with filters and pagination."""
    try:
        result = storage.search_spans(
            time_range=request.time_range, filters=request.filters, pagination=request.pagination
        )

        # Handle case where storage returns unexpected format
        if not isinstance(result, tuple) or len(result) != 3:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage returned invalid result format",
            )

        spans, has_more, next_cursor = result

        return SpanSearchResponse(
            spans=spans,
            pagination=PaginationResponse(has_more=has_more, next_cursor=next_cursor, total_count=len(spans)),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search spans: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search spans: {e!s}",
        ) from e


@router.post("/logs/search", response_model=LogSearchResponse)
def search_logs(request: LogSearchRequest, storage: StorageBackend = Depends(get_storage)):
    """Search logs with filters and pagination."""
    try:
        result = storage.search_logs(
            time_range=request.time_range, filters=request.filters, pagination=request.pagination
        )

        if not isinstance(result, tuple) or len(result) != 3:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage returned invalid result format",
            )

        logs, has_more, next_cursor = result

        return LogSearchResponse(
            logs=logs,
            pagination=PaginationResponse(has_more=has_more, next_cursor=next_cursor, total_count=len(logs)),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {e!s}",
        ) from e


@router.post("/metrics/search", response_model=MetricSearchResponse)
def search_metrics(request: MetricSearchRequest, storage: StorageBackend = Depends(get_storage)):
    """Search metrics with filters and pagination."""
    try:
        result = storage.search_metrics(
            time_range=request.time_range,
            metric_names=request.metric_names,
            filters=request.filters,
            pagination=request.pagination,
        )

        if not isinstance(result, tuple) or len(result) != 3:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage returned invalid result format",
            )

        metrics, has_more, next_cursor = result

        return MetricSearchResponse(
            metrics=metrics,
            pagination=PaginationResponse(has_more=has_more, next_cursor=next_cursor, total_count=len(metrics)),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search metrics: {e!s}",
        ) from e


@router.post("/metrics/{metric_name}/detail")
def get_metric_detail(
    metric_name: str,
    request: MetricSearchRequest,
    storage: StorageBackend = Depends(get_storage),
):
    """Get detailed time-series data for a specific metric.

    Set include_attributes=true in request body to include unique attribute combinations
    for cardinality analysis.
    """
    try:
        # Get metric detail from storage
        result = storage.get_metric_detail(
            metric_name=metric_name,
            time_range=request.time_range,
            filters=request.filters,
            include_attributes=request.include_attributes,
        )

        if result is None:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric detail: {e!s}",
        ) from e


@router.post("/services", response_model=ServiceListResponse)
def list_services(
    request: ServiceSearchRequest = ServiceSearchRequest(), storage: StorageBackend = Depends(get_storage)
):
    """List services with RED metrics for optional time range and namespace filters."""
    try:
        services = storage.get_services(time_range=request.time_range, filters=request.filters)

        return ServiceListResponse(services=services, total_count=len(services))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list services: {e!s}",
        ) from e


@router.post("/service-map", response_model=ServiceMapResponse)
def get_service_map(
    request: ServiceSearchRequest = ServiceSearchRequest(), storage: StorageBackend = Depends(get_storage)
):
    """Get service dependency map for time range with optional namespace filters."""
    try:
        # Service map requires time_range
        if request.time_range is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="time_range is required for service-map"
            )

        result = storage.get_service_map(time_range=request.time_range, filters=request.filters)

        if not isinstance(result, tuple) or len(result) != 2:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage returned invalid result format",
            )

        nodes, edges = result

        return ServiceMapResponse(nodes=nodes, edges=edges, time_range=request.time_range)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service map: {e!s}",
        ) from e


@router.get("/namespaces")
def get_namespaces(storage: StorageBackend = Depends(get_storage)):
    """Get list of all namespaces for filtering."""
    try:
        namespaces = storage.get_namespaces()
        return {"namespaces": namespaces}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get namespaces: {e!s}",
        ) from e
