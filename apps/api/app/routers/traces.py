"""Traces query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
TracesStorage and v_otel_spans_enriched view.
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session

from app.dependencies import get_db_session
from app.models.api import PaginationResponse, TraceSearchRequest, TraceSearchResponse
from app.storage.traces_storage import TracesStorage

router = APIRouter(prefix="/traces", tags=["traces"])
logger = logging.getLogger(__name__)


def get_traces_storage(session: Annotated[Session, Depends(get_db_session)]) -> TracesStorage:
    """Dependency to get TracesStorage instance."""
    return TracesStorage(session)


def rfc3339_to_nanoseconds(rfc3339_str: str) -> int:
    """Convert RFC3339 timestamp to Unix nanoseconds."""
    dt = datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1_000_000_000)


@router.post("/search", response_model=TraceSearchResponse)
def search_traces(
    request: TraceSearchRequest,
    traces_storage: Annotated[TracesStorage, Depends(get_traces_storage)],
):
    """Search traces with filters using OTLP schema.

    Request body includes:
    - time_range: Start/end times in RFC3339 format
    - filters: Optional filters (service.name, min_duration)
    - pagination: Limit and cursor

    Response includes:
    - traces: Array of trace summaries
    - pagination: Has_more flag and next cursor
    """
    try:
        # Convert RFC3339 to nanoseconds
        start_time = rfc3339_to_nanoseconds(request.time_range.start_time)
        end_time = rfc3339_to_nanoseconds(request.time_range.end_time)

        # Extract filters
        service_name = None
        min_duration = None

        if request.filters:
            for f in request.filters:
                if f.field == "service.name" and f.operator == "eq":
                    service_name = str(f.value)
                elif f.field == "duration" and f.operator == "gte":
                    # Convert seconds to nanoseconds if needed
                    min_duration = (
                        int(float(f.value) * 1_000_000_000) if isinstance(f.value, (int, float)) else int(f.value)
                    )

        # Query storage
        traces = traces_storage.get_traces(
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
            min_duration=min_duration,
            limit=request.pagination.limit,
            offset=0,
        )

        return TraceSearchResponse(
            traces=traces,
            pagination=PaginationResponse(
                has_more=len(traces) == request.pagination.limit,
                next_cursor=None,
                total_count=None,
            ),
        )

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
