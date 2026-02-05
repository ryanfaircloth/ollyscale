"""v2 logs query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
LogsStorage and v_otel_logs_enriched view. They coexist with v1 endpoints
until Phase 5 migration.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session

from app.dependencies import get_db_session
from app.storage.logs_storage import LogsStorage

router = APIRouter(prefix="/v2/logs", tags=["logs-v2"])
logger = logging.getLogger(__name__)


def get_logs_storage(session: Annotated[Session, Depends(get_db_session)]) -> LogsStorage:
    """Dependency to get LogsStorage instance."""
    return LogsStorage(session)


@router.get("/search")
def search_logs_v2(
    start_time: Annotated[int, Query(description="Start time in nanoseconds since Unix epoch")],
    end_time: Annotated[int, Query(description="End time in nanoseconds since Unix epoch")],
    severity_min: Annotated[int | None, Query(description="Minimum severity number (1-24)", ge=1, le=24)] = None,
    trace_id: Annotated[str | None, Query(description="Filter by trace ID", max_length=32)] = None,
    service_name: Annotated[str | None, Query(description="Filter by service name")] = None,
    limit: Annotated[int, Query(description="Maximum number of results", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Result offset for pagination", ge=0)] = 0,
    logs_storage: Annotated[LogsStorage, Depends(get_logs_storage)] = None,
):
    """Search logs with filters using v2 OTLP schema.

    Returns logs with enriched attributes from typed tables and JSONB catch-all.
    Uses v_otel_logs_enriched view for efficient querying.

    Query parameters:
    - start_time, end_time: Time range in nanoseconds (required)
    - severity_min: Filter logs with severity >= this value
    - trace_id: Filter logs by trace correlation
    - service_name: Filter logs by service
    - limit: Max results (default 100, max 1000)
    - offset: Pagination offset (default 0)

    Response includes:
    - log_id, timestamps, severity, body
    - trace_id, span_id for correlation
    - attributes: All attributes (promoted + other) as JSONB
    - resource_attributes: Service context
    - scope_attributes: Instrumentation library
    - semantic_type: Detected type (ai_agent, http, db, messaging, general)
    """
    try:
        logs = logs_storage.get_logs(
            start_time=start_time,
            end_time=end_time,
            severity_min=severity_min,
            trace_id=trace_id,
            service_name=service_name,
            limit=limit,
            offset=offset,
        )

        return {
            "logs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset,
            "has_more": len(logs) == limit,  # If full page, more might exist
        }

    except Exception as e:
        logger.exception("Failed to search logs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {e!s}",
        ) from e


@router.get("/trace/{trace_id}")
def get_logs_by_trace_v2(
    trace_id: Annotated[str, Path(description="Trace ID (32-char hex)", min_length=32, max_length=32)],
    logs_storage: Annotated[LogsStorage, Depends(get_logs_storage)] = None,
):
    """Get all logs for a trace, grouped by span.

    Returns a hierarchical structure:
    {
        "trace_id": "...",
        "logs_count": 42,
        "spans": {
            "span_id_1": [log1, log2, ...],
            "span_id_2": [log3, log4, ...],
            "null": [orphan_log1, ...]  # Logs without span_id
        }
    }

    This helps correlate logs with specific spans in a trace.
    """
    try:
        # Get all logs for this trace
        logs = logs_storage.get_logs(
            start_time=0,  # No time filter when querying by trace_id
            end_time=9999999999999999999,
            trace_id=trace_id,
            limit=10000,  # High limit for full trace
        )

        if not logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No logs found for trace {trace_id}",
            )

        # Group logs by span_id
        spans = {}
        for log in logs:
            span_id = log.get("span_id_hex") or "null"
            if span_id not in spans:
                spans[span_id] = []
            spans[span_id].append(log)

        return {
            "trace_id": trace_id,
            "logs_count": len(logs),
            "spans": spans,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get logs by trace")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs by trace: {e!s}",
        ) from e


@router.get("/trace/{trace_id}/span/{span_id}")
def get_logs_by_span_v2(
    trace_id: Annotated[str, Path(description="Trace ID (32-char hex)", min_length=32, max_length=32)],
    span_id: Annotated[str, Path(description="Span ID (16-char hex)", min_length=16, max_length=16)],
    logs_storage: Annotated[LogsStorage, Depends(get_logs_storage)] = None,
):
    """Get logs for a specific span within a trace.

    Returns all logs correlated to the given trace_id and span_id.
    Useful for detailed span analysis and debugging.
    """
    try:
        # Query logs with both trace_id and span_id filter
        # For now, get all trace logs and filter client-side
        # TODO: Add span_id filter to LogsStorage.get_logs() in future optimization
        logs = logs_storage.get_logs(
            start_time=0,
            end_time=9999999999999999999,
            trace_id=trace_id,
            limit=10000,
        )

        # Filter to specific span
        span_logs = [log for log in logs if log.get("span_id_hex") == span_id]

        if not span_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No logs found for trace {trace_id}, span {span_id}",
            )

        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "logs_count": len(span_logs),
            "logs": span_logs,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get logs by span")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs by span: {e!s}",
        ) from e
