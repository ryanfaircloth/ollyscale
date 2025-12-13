# TinyOlly UI Refactoring Plan

## Overview

**Current state:** 2125 lines in a single `tinyolly-ui.py` file
**Goal:** Modular structure following FastAPI best practices with clear separation of concerns

## Proposed Structure

```
tinyolly-ui/
├── app/
│   ├── __init__.py              # App factory
│   ├── main.py                  # Entry point, app creation, router registration
│   ├── config.py                # Settings and environment variables
│   ├── dependencies.py          # Shared dependencies (storage, managers)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── middleware.py        # HTTP middleware (metrics, CORS, GZip)
│   │   ├── telemetry.py         # OpenTelemetry metrics setup
│   │   └── logging.py           # Logging configuration
│   │
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── websocket.py         # ConnectionManager for WebSocket
│   │   └── alerts.py            # AlertManager class
│   │
│   ├── routers/
│   │   ├── __init__.py          # Router exports
│   │   ├── ingest.py            # POST /v1/traces, /v1/logs, /v1/metrics
│   │   ├── query.py             # GET endpoints for traces, spans, logs, metrics
│   │   ├── services.py          # Service map, catalog, stats
│   │   ├── admin.py             # Admin stats, alerts CRUD
│   │   ├── system.py            # Health, WebSocket, index page
│   │   └── opamp.py             # All OpAMP endpoints
│   │
│   └── services/
│       ├── __init__.py
│       └── validation.py        # OTel config validation helpers
│
├── models.py                    # Keep as-is (already separated)
├── templates/                   # Keep as-is
├── static/                      # Keep as-is
└── tinyolly-ui.py              # Thin wrapper: imports and runs app
```

## File Breakdown

### 1. `app/config.py` (~40 lines)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6579

    # Server
    port: int = 5002
    log_level: str = "INFO"

    # OpAMP
    opamp_server_url: str = "http://localhost:4321"
    otelcol_default_config: str = "/app/otelcol-config.yaml"
    otelcol_templates_dir: str = "/app/otelcol-templates"

    # OTLP
    otel_exporter_otlp_metrics_endpoint: str = "http://localhost:5001/v1/metrics"

    # Deployment
    deployment_env: str = "docker"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. `app/core/telemetry.py` (~50 lines)
Extract lines 42-91: OpenTelemetry metrics setup
- `meter`, `request_counter`, `error_counter`, `response_time_histogram`, etc.

### 3. `app/core/middleware.py` (~40 lines)
Extract lines 176-214: `metrics_middleware`
- Middleware that records request metrics

### 4. `app/managers/websocket.py` (~60 lines)
Extract lines 246-297: `ConnectionManager` class
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket): ...
    def disconnect(self, websocket: WebSocket): ...
    async def broadcast(self, message: dict): ...
```

### 5. `app/managers/alerts.py` (~140 lines)
Extract lines 303-433: `AlertManager` class
- Alert rule management
- Redis storage for alerts
- Periodic alert checking

### 6. `app/dependencies.py` (~30 lines)
Shared dependencies using FastAPI's dependency injection:
```python
from functools import lru_cache
from tinyolly_common import Storage
from .config import settings
from .managers.websocket import ConnectionManager
from .managers.alerts import AlertManager

@lru_cache()
def get_storage() -> Storage:
    return Storage(host=settings.redis_host, port=settings.redis_port)

# Singleton instances
connection_manager = ConnectionManager()
alert_manager: AlertManager = None  # Initialized after storage

def get_connection_manager() -> ConnectionManager:
    return connection_manager

def get_alert_manager() -> AlertManager:
    return alert_manager
```

### 7. `app/routers/ingest.py` (~180 lines)
Extract OTLP ingestion endpoints:
- `POST /v1/traces` (lines 461-533)
- `POST /v1/logs` (lines 535-593)
- `POST /v1/metrics` (lines 595-676)

```python
from fastapi import APIRouter, Request, Depends
from ..dependencies import get_storage

router = APIRouter(prefix="/v1", tags=["Ingestion"])

@router.post("/traces")
async def ingest_traces(request: Request, storage = Depends(get_storage)): ...
```

### 8. `app/routers/query.py` (~300 lines)
Extract query endpoints:
- `GET /api/traces` (lines 678-706)
- `GET /api/traces/{trace_id}` (lines 708-738)
- `GET /api/spans` (lines 740-775)
- `GET /api/logs` (lines 777-799)
- `GET /api/logs/stream` (lines 801-875)
- `GET /api/metrics` (lines 877-919)
- `GET /api/metrics/{name}` (lines 921-962)
- `GET /api/metrics/query` (lines 964-1032)
- `GET /api/metrics/{name}/resources` (lines 1034-1053)
- `GET /api/metrics/{name}/attributes` (lines 1055-1095)

### 9. `app/routers/services.py` (~80 lines)
Extract service-related endpoints:
- `GET /api/service-map` (lines 1097-1120)
- `GET /api/service-catalog` (lines 1122-1144)
- `GET /api/stats` (lines 1146-1180)

### 10. `app/routers/admin.py` (~100 lines)
Extract admin endpoints:
- `GET /admin/stats` (lines 1233-1262)
- `GET /api/alerts` (lines 1264-1273)
- `POST /api/alerts` (lines 1275-1310)
- `DELETE /api/alerts/{name}` (lines 1312-1321)

### 11. `app/routers/system.py` (~100 lines)
Extract system endpoints:
- `GET /` - index page (lines 1218-1231)
- `GET /health` (lines 1378-1419)
- `WebSocket /ws/updates` (lines 1323-1376)

### 12. `app/routers/opamp.py` (~350 lines)
Extract all OpAMP endpoints:
- `GET /api/opamp/status` (lines 1421-1458)
- `GET /api/opamp/config` (lines 1460-1501)
- `POST /api/opamp/validate` (lines 1512-1603)
- `POST /api/opamp/config` (lines 1863-1925)
- `GET /api/opamp/health` (lines 1927-1968)
- `GET /api/opamp/templates` (lines 1970-2053)
- `GET /api/opamp/templates/{id}` (lines 2055-2125)

Also include request/response models:
- `ConfigValidateRequest`
- `ConfigUpdateRequest`

### 13. `app/services/validation.py` (~200 lines)
Extract validation helpers:
- `_format_otelcol_errors()` (lines 1605-1803)
- `_basic_validation()` (lines 1805-1861)

### 14. `app/main.py` (~80 lines)
Main app factory:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .core.middleware import setup_middleware
from .core.telemetry import setup_telemetry
from .dependencies import get_storage, connection_manager
from .managers.alerts import AlertManager
from .routers import ingest, query, services, admin, system, opamp

def create_app() -> FastAPI:
    app = FastAPI(
        title="TinyOlly",
        description="Minimal observability backend",
        default_response_class=ORJSONResponse
    )

    # Setup
    setup_telemetry()
    setup_middleware(app)

    # Static files and templates
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    # Initialize storage and managers
    storage = get_storage()
    alert_manager = AlertManager(storage, connection_manager)

    # Register routers
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(services.router)
    app.include_router(admin.router)
    app.include_router(system.router)
    app.include_router(opamp.router)

    return app

app = create_app()
```

### 15. `tinyolly-ui.py` (~10 lines)
Thin entry point wrapper:
```python
"""TinyOlly UI - Entry Point"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
```

## Implementation Order

### Phase 1: Foundation (No breaking changes)
1. Create `app/` directory structure
2. `app/config.py` - Extract settings
3. `app/core/logging.py` - Extract logging setup
4. `app/core/telemetry.py` - Extract metrics setup

### Phase 2: Core Components
5. `app/managers/websocket.py` - Extract ConnectionManager
6. `app/managers/alerts.py` - Extract AlertManager
7. `app/dependencies.py` - Create dependency injection

### Phase 3: Services
8. `app/services/validation.py` - Extract validation helpers

### Phase 4: Routers (Can be parallelized)
9. `app/routers/ingest.py`
10. `app/routers/query.py`
11. `app/routers/services.py`
12. `app/routers/admin.py`
13. `app/routers/system.py`
14. `app/routers/opamp.py`

### Phase 5: Integration
15. `app/main.py` - Wire everything together
16. Update `tinyolly-ui.py` to use new structure
17. Update Dockerfile if needed

## Testing Strategy

After each phase:
1. Run the app locally
2. Test affected endpoints with curl/httpie
3. Verify no import errors
4. Check logs for warnings

Key endpoints to test:
```bash
# Health
curl http://localhost:5002/health

# Ingestion
curl -X POST http://localhost:5002/v1/traces -d '{}'

# Queries
curl http://localhost:5002/api/traces
curl http://localhost:5002/api/metrics

# OpAMP
curl http://localhost:5002/api/opamp/status
curl http://localhost:5002/api/opamp/templates
```

## Key Improvements Over Cursor's Plan

1. **Uses `pydantic-settings`** for type-safe configuration
2. **Proper dependency injection** via FastAPI's `Depends()`
3. **App factory pattern** (`create_app()`) for testability
4. **Cleaner router organization** - query endpoints grouped together
5. **Core module** for cross-cutting concerns (logging, telemetry, middleware)
6. **Thin entry point** - keeps `tinyolly-ui.py` minimal for backwards compatibility

## Notes

- Keep `models.py` as-is (already well-organized)
- Static files and templates stay in place
- Dockerfile CMD can remain unchanged (`tinyolly-ui:app`)
- All routers should use `tags=["..."]` for OpenAPI grouping
