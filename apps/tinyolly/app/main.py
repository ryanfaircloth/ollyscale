# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
        title="TinyOlly API",
        version="2.0.0",
        description="""
# TinyOlly API - Lightweight OpenTelemetry Observability Backend

TinyOlly is a lightweight OpenTelemetry-native observability backend built from scratch
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

This is the API backend. The web UI is served by the tinyolly-ui nginx container.
        """,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "TinyOlly Project",
            "url": "https://github.com/tinyolly/tinyolly",
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
