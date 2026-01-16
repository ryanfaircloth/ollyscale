# ollyScale - Observability Platform for Local Development
# Copyright (c) 2026 Ryan Faircloth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Based on ollyScale (BSD-3-Clause), see LICENSE-BSD3-ORIGINAL
# Original: https://github.com/ollyscale/ollyscale

"""Main FastAPI application factory"""

import asyncio

import uvloop
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .core.logging import setup_logging
from .core.middleware import setup_middleware
from .core.telemetry import setup_telemetry
from .routers import admin, ingest, opamp, query, services, system

# Install uvloop policy for faster event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# Setup logging
setup_logging()

# Setup telemetry
setup_telemetry()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="OllyScale API",
        version="2.0.0",
        description="""
# OllyScale API - Lightweight OpenTelemetry Observability Backend

OllyScale is a lightweight OpenTelemetry-native observability backend built from scratch
to visualize and correlate logs, metrics, and traces. Perfect for local development.

## Features

* 📊 **Traces** - Distributed tracing with span visualization
* 📝 **Logs** - Structured logging with trace correlation
* 📈 **Metrics** - Time-series metrics with full OTLP support
* 🗺️ **Service Map** - Auto-generated service dependency graphs
* 🔍 **Service Catalog** - RED metrics (Rate, Errors, Duration)

## OpenTelemetry Native

All data is stored and returned in standard OpenTelemetry format, ensuring
compatibility with OTLP exporters and OpenTelemetry SDKs.

## Note

This is the API backend. The web UI is served by the ollyscale-ui nginx container.
        """,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "OllyScale Project",
            "url": "https://github.com/ryanfaircloth/ollyscale",
        },
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        openapi_tags=[
            {"name": "Ingestion", "description": "OTLP endpoints for ingesting telemetry data (traces, logs, metrics)"},
            {"name": "Traces", "description": "Query and retrieve trace data"},
            {"name": "Spans", "description": "Query and retrieve individual span data"},
            {"name": "Logs", "description": "Query and retrieve log entries with trace correlation"},
            {"name": "Metrics", "description": "Query and retrieve time-series metrics data"},
            {"name": "Services", "description": "Service catalog, service map, and RED metrics"},
            {"name": "System", "description": "Health checks and system status"},
            {
                "name": "OpAMP",
                "description": "OpenTelemetry Agent Management Protocol - manage collector configuration",
            },
        ],
    )

    # Setup middleware
    setup_middleware(app)

    # Register API routers
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(services.router)
    app.include_router(admin.router)
    app.include_router(system.router)
    app.include_router(opamp.router)

    return app


# Create app instance
app = create_app()
