"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health():
    """Overall health status."""
    return {
        "status": "healthy",
        "database": "not_configured",  # Will be updated when DB is connected
        "migrations": "not_applicable",
        "version": "2.0.0",
    }


@router.get("/db")
def health_db():
    """Database health status."""
    return {
        "connected": False,  # Will be updated when DB is connected
        "pool_size": 0,
        "pool_active": 0,
        "migrations_applied": 0,
        "latest_migration": None,
    }
