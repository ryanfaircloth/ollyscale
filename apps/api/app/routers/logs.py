"""Logs query endpoints using new OTLP schema.

These endpoints use the new denormalized attribute architecture with
LogsStorage and v_otel_logs_enriched view.
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session

from app.dependencies import get_db_session
from app.models.api import LogRecord, LogSearchRequest, LogSearchResponse, PaginationResponse
from app.storage.logs_storage import LogsStorage

router = APIRouter(prefix="/logs", tags=["logs"])
logger = logging.getLogger(__name__)


def get_logs_storage(session: Annotated[Session, Depends(get_db_session)]) -> LogsStorage:
    """Dependency to get LogsStorage instance."""
    return LogsStorage(session)


def rfc3339_to_nanoseconds(rfc3339_str: str) -> int:
    """Convert RFC3339 timestamp to Unix nanoseconds."""
    dt = datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1_000_000_000)


def nanoseconds_to_rfc3339(nanos: int) -> str:
    """Convert Unix nanoseconds to RFC3339 timestamp."""
    seconds = nanos / 1_000_000_000
    dt = datetime.fromtimestamp(seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@router.post("/search", response_model=LogSearchResponse)
def search_logs(
    request: LogSearchRequest,
    logs_storage: Annotated[LogsStorage, Depends(get_logs_storage)],
):
    """Search logs with filters using OTLP schema.

    Request body includes:
    - time_range: Start/end times in RFC3339 format
    - filters: Optional filters (severity, trace_id, service.name)
    - pagination: Limit and cursor

    Response includes:
    - logs: Array of log records with RFC3339 timestamps
    - pagination: Has_more flag and next cursor
    """
    try:
        # Convert RFC3339 to nanoseconds
        start_time = rfc3339_to_nanoseconds(request.time_range.start_time)
        end_time = rfc3339_to_nanoseconds(request.time_range.end_time)

        # Extract filters
        severity_min = None
        trace_id = None
        service_name = None

        if request.filters:
            for f in request.filters:
                if f.field == "severity_number" and f.operator == "gte":
                    severity_min = int(f.value)
                elif f.field == "trace_id" and f.operator == "eq":
                    trace_id = str(f.value)
                elif f.field == "service.name" and f.operator == "eq":
                    service_name = str(f.value)

        # Query storage
        logs = logs_storage.get_logs(
            start_time=start_time,
            end_time=end_time,
            severity_min=severity_min,
            trace_id=trace_id,
            service_name=service_name,
            limit=request.pagination.limit,
            offset=0,  # TODO: cursor-based pagination
        )

        # Convert to API models with RFC3339 timestamps
        log_records = []
        for log in logs:
            log_records.append(
                LogRecord(
                    log_id=str(log.get("log_id")),
                    timestamp=nanoseconds_to_rfc3339(log["time_unix_nano"]),
                    observed_timestamp=nanoseconds_to_rfc3339(log["observed_time_unix_nano"])
                    if log.get("observed_time_unix_nano")
                    else None,
                    severity_number=log.get("severity_number"),
                    severity_text=log.get("severity_text"),
                    body=log.get("body"),
                    attributes=[{"key": k, "value": v} for k, v in (log.get("attributes") or {}).items()],
                    trace_id=log.get("trace_id"),
                    span_id=log.get("span_id_hex"),
                    service_name=log.get("service_name"),
                    resource=log.get("resource_attributes"),
                    scope=log.get("scope_attributes"),
                )
            )

        return LogSearchResponse(
            logs=log_records,
            pagination=PaginationResponse(
                has_more=len(logs) == request.pagination.limit,
                next_cursor=None,  # TODO: implement cursors
                total_count=None,
            ),
        )

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
