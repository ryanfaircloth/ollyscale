"""v2 traces query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
TracesStorage and v_otel_spans_enriched view. They coexist with v1 endpoints
until Phase 5 migration.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session

from app.dependencies import get_db_session
from app.storage.traces_storage import TracesStorage

router = APIRouter(prefix="/v2/traces", tags=["traces-v2"])
logger = logging.getLogger(__name__)


def get_traces_storage(session: Annotated[Session, Depends(get_db_session)]) -> TracesStorage:
    """Dependency to get TracesStorage instance."""
    return TracesStorage(session)


@router.get("/search")
def search_traces_v2(
    start_time: Annotated[int, Query(description="Start time in nanoseconds since Unix epoch")],
    end_time: Annotated[int, Query(description="End time in nanoseconds since Unix epoch")],
    service_name: Annotated[str | None, Query(description="Filter by service name")] = None,
    min_duration_ns: Annotated[int | None, Query(description="Minimum trace duration in nanoseconds", ge=0)] = None,
    limit: Annotated[int, Query(description="Maximum number of results", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Result offset for pagination", ge=0)] = 0,
    traces_storage: Annotated[TracesStorage, Depends(get_traces_storage)] = None,
):
    """Search traces with filters using v2 OTLP schema.

    Returns trace summaries with aggregated metrics (span count, duration, service).
    Uses v_otel_spans_enriched view for efficient querying.

    Query parameters:
    - start_time, end_time: Time range in nanoseconds (required)
    - service_name: Filter traces by service
    - min_duration_ns: Filter traces with duration >= this value
    - limit: Max results (default 100, max 1000)
    - offset: Pagination offset (default 0)

    Response includes:
    - trace_id: Unique trace identifier
    - span_count: Number of spans in trace
    - start_time_ns: Earliest span start time
    - end_time_ns: Latest span end time
    - duration_ns: Trace duration (end - start)
    - service_name: Primary service (from root span resource)
    """
    try:
        traces = traces_storage.get_traces(
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
            min_duration_ns=min_duration_ns,
            limit=limit,
            offset=offset,
        )

        return {
            "traces": traces,
            "count": len(traces),
            "limit": limit,
            "offset": offset,
            "has_more": len(traces) == limit,  # If full page, more might exist
        }

    except Exception as e:
        logger.exception("Failed to search traces")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search traces: {e!s}",
        ) from e


@router.get("/{trace_id}/spans")
def get_trace_spans_v2(
    trace_id: Annotated[str, Path(description="Trace ID (32-char hex)", min_length=32, max_length=32)],
    traces_storage: Annotated[TracesStorage, Depends(get_traces_storage)] = None,
):
    """Get all spans for a trace with full details.

    Returns spans in chronological order with parent_span_id_hex for tree construction.
    Includes all attributes (promoted + other) and resource/scope context.

    Response structure:
    {
        "trace_id": "...",
        "spans_count": 42,
        "spans": [
            {
                "span_id": 123,
                "span_id_hex": "abc123...",
                "parent_span_id_hex": "def456..." or null,
                "name": "GET /api/users",
                "kind": 2,  # SpanKind enum
                "start_time_unix_nano": 1234567890000000000,
                "end_time_unix_nano": 1234567890123456789,
                "duration_ns": 123456789,
                "status_code": 0,  # StatusCode enum
                "status_message": null or "error details",
                "attributes": {...},  # All promoted + other attrs
                "resource_attributes": {...},
                "scope_attributes": {...},
                "service_name": "my-service",
                "semantic_type": "http"
            },
            ...
        ]
    }

    Spans are ordered by start_time_unix_nano ASC for timeline rendering.
    Use parent_span_id_hex to build trace tree structure on client side.
    """
    try:
        spans = traces_storage.get_trace_spans(trace_id=trace_id)

        if not spans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No spans found for trace {trace_id}",
            )

        # Calculate duration for each span
        for span in spans:
            span["duration_ns"] = span["end_time_unix_nano"] - span["start_time_unix_nano"]

        return {
            "trace_id": trace_id,
            "spans_count": len(spans),
            "spans": spans,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get trace spans")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trace spans: {e!s}",
        ) from e
