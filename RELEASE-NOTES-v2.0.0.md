# TinyOlly v2.0.0

**Release Date:** December 2024

Major update to TinyOlly with comprehensive OpenAPI enhancements, making the REST API production-ready with full documentation, type safety, and SDK generation support.

---

## What's New

### Docker Hub Deployment

TinyOlly now uses Docker Hub for faster, more consistent deployments:

#### Pre-Built Images
- **All images on Docker Hub**: `tinyolly/*` organization
- **Multi-architecture**: linux/amd64, linux/arm64 (Apple Silicon)
- **Faster deployment**: ~30 seconds vs 5-10 minutes
- **Version tags**: `:latest` and semantic versions (e.g., `:v2.0.0`)

#### Images Available
- `tinyolly/python-base` - Shared Python base image
- `tinyolly/ui` - TinyOlly web UI
- `tinyolly/otlp-receiver` - OTLP data receiver
- `tinyolly/opamp-server` - OpAMP configuration server
- `tinyolly/otel-supervisor` - OpenTelemetry Collector with OpAMP
- `tinyolly/demo-frontend` - Demo frontend application
- `tinyolly/demo-backend` - Demo backend service
- `tinyolly/ai-agent-demo` - AI agent with GenAI instrumentation

#### Developer Benefits
- **Instant deployment**: No build time required
- **Consistent images**: Same across all environments
- **Local builds optional**: Use `-local` scripts for development
- **Cross-platform**: Works on Intel and ARM Macs

### OpenAPI & REST API Enhancements

This release dramatically improves the REST API with professional-grade OpenAPI documentation:

#### Type Safety & Validation
- **13 Pydantic Models**: Complete request/response validation
  - `ErrorResponse`, `HealthResponse`, `IngestResponse`
  - `TraceDetail`, `TraceSummary`, `SpanDetail`
  - `LogEntry`, `MetricMetadata`, `MetricDetail`, `MetricQueryResult`
  - `ServiceMap`, `ServiceCatalogEntry`, `StatsResponse`
- **Automatic Validation**: All endpoints now validate inputs and outputs
- **IDE Support**: Full autocomplete and type checking

#### Comprehensive Documentation
- **All 20 endpoints** fully documented with detailed descriptions
- **Request/Response Schemas**: Every endpoint shows exactly what to send and expect
- **Code Examples**: Markdown examples showing how to use each endpoint
- **Error Documentation**: All possible HTTP status codes documented
- **Parameter Descriptions**: Every query parameter explained with limits and defaults

#### Better Organization
- **7 API Tags**: Endpoints organized into logical categories
  - Ingestion (OTLP data ingestion)
  - Traces (query traces)
  - Spans (query spans)
  - Logs (query and stream logs)
  - Metrics (query metrics)
  - Services (catalog and map)
  - System (health and stats)
- **Operation IDs**: Unique identifiers for all endpoints (perfect for code generation)
- **Rich Metadata**: Contact info, license, comprehensive descriptions

#### SDK Generation Ready
- **OpenAPI 3.0 Compliant**: Full, valid OpenAPI specification
- **Client Generation**: Generate SDKs in any language using OpenAPI Generator
- **Tool Compatible**: Works with Postman, Insomnia, Swagger Editor, etc.

#### Enhanced Developer Experience
- **Interactive Swagger UI**: Try endpoints directly in the browser
- **ReDoc Interface**: Beautiful, searchable API documentation
- **Schema Examples**: Every model includes example data
- **Response Models**: All endpoints declare return types

---

## Technical Improvements

### Code Quality
- **Missing Import Fixed**: Added `StreamingResponse` import (was causing runtime errors)
- **Status Codes**: Added `status` module import for HTTP status code constants
- **Type Hints**: Enhanced with `Literal` types for enum-like fields

### API Enhancements
- **Parameter Validation**: Max limits on pagination (e.g., `le=1000`)
- **Default Values**: Clear defaults documented for all parameters
- **Error Standardization**: Consistent error response format across all endpoints
- **Response Codes**: All endpoints document possible HTTP responses

### Documentation Updates
- **README Enhanced**: New section highlighting OpenAPI features
- **SDK Generation Guide**: Instructions for generating client libraries
- **API Feature List**: Complete list of API capabilities

---

## Files Modified

### Core Application
- `/docker/apps/tinyolly-ui/tinyolly-ui.py` - Enhanced with full OpenAPI support
- `/docker-core-only/apps/tinyolly-ui/tinyolly-ui.py` - Enhanced with full OpenAPI support

### Docker Hub Migration
- All `docker-compose*.yml` files - Updated to use Docker Hub images
- All deployment scripts - Updated to pull from Docker Hub
- Kubernetes manifests - Updated for Docker Hub images
- Build scripts - Created for publishing to Docker Hub

### Documentation
- `/README.md` - Updated with Docker Hub and OpenAPI improvements
- `/docs/docker.md` - Updated deployment instructions
- `/docs/kubernetes.md` - Updated for Docker Hub deployment

---

## Highlights

### Before v2.0.0
```python
@app.get('/api/traces', tags=["Traces"])
async def get_traces(limit: int = Query(default=100)):
    """Get list of recent traces with summaries"""
```

### After v2.0.0
```python
@app.get(
    '/api/traces',
    tags=["Traces"],
    response_model=List[Dict[str, Any]],
    operation_id="get_traces",
    summary="Get recent traces",
    responses={
        200: {"description": "List of trace summaries"}
    }
)
async def get_traces(
    limit: int = Query(default=100, le=1000, 
                      description="Maximum number of traces to return (max 1000)")
):
    """
    Get list of recent traces with summaries.
    
    Returns trace metadata including root service, operation name, duration, 
    span count, and error status. Results are sorted by most recent first.
    """
```

---

## Documentation Access

After starting TinyOlly, access the enhanced API documentation:

- **Swagger UI**: http://localhost:5005/docs
  - Interactive API explorer
  - Try endpoints directly
  - See all models and examples

- **ReDoc**: http://localhost:5005/redoc
  - Clean, three-panel documentation
  - Better for reading and reference

- **OpenAPI JSON**: http://localhost:5005/openapi.json
  - Machine-readable schema
  - Use with code generators
  - Import into Postman, Insomnia, etc.

---

## Upgrade Instructions

### From v1.0.0

TinyOlly v2.0.0 is **100% backward compatible** with v1.0.0. No breaking changes to:
- API endpoints (all URLs remain the same)
- Data formats
- Functionality or business logic

**Major change**: Now uses Docker Hub by default for faster deployment.

```bash
# Pull latest changes
git pull origin main

# Docker - Now pulls images from Docker Hub (~30 seconds)
cd docker
./02-stop-core.sh
./01-start-core.sh

# Or Kubernetes - Now pulls images from Docker Hub
cd k8s
./03-cleanup.sh
./02-deploy-tinyolly.sh
```

**For local development**: Use `-local` variants of deployment scripts to build images locally:
```bash
# Docker local builds
cd docker
./01-start-core-local.sh

# Demo apps local builds
cd docker-demo
./01-deploy-demo-local.sh
```

No configuration changes required!

---

## New Capabilities

### Generate API Clients

Now you can generate type-safe client libraries in any language:

```bash
# Download OpenAPI spec
curl http://localhost:5005/openapi.json > openapi.json

# Generate Python client
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./tinyolly-python-client

# Generate TypeScript client
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-fetch \
  -o ./tinyolly-ts-client

# Generate Go client
openapi-generator-cli generate \
  -i openapi.json \
  -g go \
  -o ./tinyolly-go-client
```

### Import into API Tools

- **Postman**: Import `/openapi.json` to get instant collection
- **Insomnia**: Import spec for full API exploration
- **Swagger Editor**: Validate and customize the spec
- **API Testing**: Use with Dredd, Prism, or other tools

---

## Statistics

### API Improvements
- **20 endpoints** fully documented
- **13 Pydantic models** with validation and examples
- **7 API tags** for organization
- **60+ improvements** across all endpoints

### Docker Hub Migration
- **8 images** published to Docker Hub
- **2 architectures** supported (amd64, arm64)
- **~30 second** deployment time (vs 5-10 minutes)
- **100% backward compatible** - 0 breaking changes

---

## Use Cases Enabled

### For Developers
- Auto-generated, always up-to-date documentation
- Type-safe client libraries in any language
- Better IDE support with autocomplete
- Clear error messages and validation

### For Integration
- OpenAPI 3.0 standard compliance
- Easy third-party tool integration
- SDK generation for any language
- Import into Postman/Insomnia

### For Production
- Comprehensive API documentation
- Request/response validation
- Standardized error handling
- Professional API presentation

---

## Future Enhancements

While v2.0.0 provides comprehensive OpenAPI support, future versions may include:
- API versioning with `/api/v1/` prefix
- Authentication (API keys, OAuth2)
- Rate limiting documentation
- GraphQL endpoint
- Webhook support

---

## Acknowledgments

TinyOlly v2.0.0 builds on the solid foundation of v1.0.0 while dramatically improving the developer experience through comprehensive OpenAPI documentation.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/tinyolly/tinyolly
cd tinyolly
git checkout v2.0.0

# Start with Docker (pulls from Docker Hub - ~30 seconds)
cd docker
./01-start-core.sh

# Deploy demo apps (optional)
cd docker-demo
./01-deploy-demo.sh

# Access the application
# - Web UI: http://localhost:5005
# - Swagger UI: http://localhost:5005/docs
# - ReDoc: http://localhost:5005/redoc
# - OpenAPI Spec: http://localhost:5005/openapi.json
```

---

## Bug Fixes

- Fixed missing `StreamingResponse` import in log streaming endpoint
- Added proper type hints throughout the codebase
- Standardized error response format

---

## Additional Resources

- [Main Documentation](https://tinyolly.github.io/tinyolly/)
- [GitHub Repository](https://github.com/tinyolly/tinyolly)
- [API Documentation](docs/api.md)
- [Docker Deployment](docs/docker.md)
- [Kubernetes Deployment](docs/kubernetes.md)

---

**Built for the OpenTelemetry community**

