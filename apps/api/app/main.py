"""
Frontend application entry point for ollyScale v2.

This application provides a Postgres-backed observability platform with
OTEL-aligned data ingestion and query APIs.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import initialize_storage
from app.routers import health, ingest, opamp, query

# Create FastAPI app instance
app = FastAPI(
    title="ollyScale v2 Frontend API",
    description="Postgres-backed observability platform with OTEL-aligned APIs",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize storage and start background readiness checker on app startup."""
    logger = logging.getLogger(__name__)
    logger.info("Application startup: initializing storage...")

    try:
        # Initialize storage (creates instance, starts readiness checker)
        # Does NOT wait for database to be ready
        initialize_storage()
        logger.info("Storage initialization complete - readiness checker started")
    except Exception as e:
        # Log errors but don't prevent startup
        # The readiness probe will fail until storage is properly configured
        logger.error(f"Storage initialization failed: {e}", exc_info=True)


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(opamp.router)  # OpAMP router includes its own prefix


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "ollyscale-frontend",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
