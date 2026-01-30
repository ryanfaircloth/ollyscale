"""Ingestion endpoints for OTLP data."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_storage
from app.models.api import LogIngestRequest, MetricIngestRequest, TraceIngestRequest
from app.storage.interface import StorageBackend

router = APIRouter()


@router.post("/traces", status_code=status.HTTP_202_ACCEPTED)
def ingest_traces(
    request: TraceIngestRequest,
    storage: StorageBackend = Depends(get_storage),
):
    """Ingest OTLP traces.

    Args:
        request: OTLP trace request with resource_spans
        storage: Storage backend (injected)

    Returns:
        Status and count of stored spans

    Raises:
        HTTPException: 422 if validation fails, 500 if storage fails
    """
    if not request.resource_spans:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="resource_spans cannot be empty",
        )

    try:
        count = storage.store_traces(request.resource_spans)
        return {"status": "accepted", "count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store traces: {e!s}",
        ) from e


@router.post("/logs", status_code=status.HTTP_202_ACCEPTED)
def ingest_logs(
    request: LogIngestRequest,
    storage: StorageBackend = Depends(get_storage),
):
    """Ingest OTLP logs.

    Args:
        request: OTLP log request with resource_logs
        storage: Storage backend (injected)

    Returns:
        Status and count of stored logs

    Raises:
        HTTPException: 422 if validation fails, 500 if storage fails
    """
    if not request.resource_logs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="resource_logs cannot be empty",
        )

    try:
        count = storage.store_logs(request.resource_logs)
        return {"status": "accepted", "count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store logs: {e!s}",
        ) from e


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
def ingest_metrics(
    request: MetricIngestRequest,
    storage: StorageBackend = Depends(get_storage),
):
    """Ingest OTLP metrics.

    Args:
        request: OTLP metric request with resource_metrics
        storage: Storage backend (injected)

    Returns:
        Status and count of stored metrics

    Raises:
        HTTPException: 422 if validation fails, 500 if storage fails
    """
    if not request.resource_metrics:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="resource_metrics cannot be empty",
        )

    try:
        count = storage.store_metrics(request.resource_metrics)
        return {"status": "accepted", "count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store metrics: {e!s}",
        ) from e
