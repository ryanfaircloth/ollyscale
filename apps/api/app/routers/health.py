"""Health check endpoints."""

from fastapi import APIRouter, Response

from app import dependencies

router = APIRouter()


@router.get("/live")
def health_live():
    """Liveness probe endpoint.

    Always returns 200 OK if the process is alive.
    Use this for Kubernetes livenessProbe.
    """
    return {
        "status": "alive",
        "version": "2.0.0",
    }


@router.get("/ready")
def health_ready(response: Response):
    """Readiness probe endpoint.

    Returns 503 if database is not ready or migrations incomplete.
    Returns 200 when ready to accept traffic.
    Use this for Kubernetes readinessProbe.
    """
    # If storage not initialized yet, not ready
    if dependencies._storage is None:
        response.status_code = 503
        return {
            "status": "not_ready",
            "message": "Storage not initialized",
        }

    # Check if database is ready
    if not dependencies._storage.is_ready:
        response.status_code = 503
        status = dependencies._storage.get_readiness_status()
        return {
            "status": "not_ready",
            "message": status["message"],
            "schema_version": status.get("schema_version"),
        }

    # Ready! Check if in read-only mode
    status = dependencies._storage.get_readiness_status()
    mode = "read-only" if status.get("read_only") else "read-write"
    return {
        "status": "ready",
        "mode": mode,
        "message": status["message"],
        "schema_version": status.get("schema_version"),
        "migration_in_progress": status.get("read_only", False),
        "version": "2.0.0",
    }


@router.get("/")
def health(response: Response):
    """Overall health status (alias to /ready for backward compatibility)."""
    return health_ready(response)


@router.get("/db")
def health_db(response: Response):
    """Database health status with detailed information."""
    # If storage not initialized yet, not ready
    if dependencies._storage is None:
        response.status_code = 503
        return {
            "status": "not_initialized",
            "connected": False,
            "pool_size": 0,
            "pool_active": 0,
        }

    # Get readiness status
    readiness = dependencies._storage.get_readiness_status()

    # Get connection pool stats if available
    pool_stats = {}
    if dependencies._storage.engine:
        pool_stats = dependencies._storage.get_connection_pool_stats()

    # If not ready, return 503
    if not dependencies._storage.is_ready:
        response.status_code = 503
        return {
            "status": "not_ready",
            "message": readiness["message"],
            "connected": False,
            "schema_version": readiness.get("schema_version"),
            **pool_stats,
        }

    # Ready - return detailed stats with mode information
    mode = "read-only" if readiness.get("read_only") else "read-write"
    return {
        "status": "ready",
        "mode": mode,
        "connected": True,
        "message": readiness["message"],
        "schema_version": readiness.get("schema_version"),
        "migration_in_progress": readiness.get("read_only", False),
        **pool_stats,
    }
