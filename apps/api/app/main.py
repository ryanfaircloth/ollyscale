"""
Frontend application entry point for ollyScale v2.

This application provides a Postgres-backed observability platform with
OTEL-aligned data ingestion and query APIs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, ingest, logs, metrics, opamp, traces

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

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(traces.router, prefix="/api", tags=["traces"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
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
