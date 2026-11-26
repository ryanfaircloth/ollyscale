# Prometheus Migration Plan - Detailed Architecture

## Executive Summary

This document outlines a comprehensive plan to migrate TinyOlly's metrics storage from Redis to Prometheus, addressing performance issues with high-cardinality metrics and enabling production-ready PromQL query capabilities.

**Problem:** Current Redis-based metrics storage causes UI slowdown with high cardinality, lacks production-ready query capabilities, and limits developers from building autoscale/monitoring patterns.

**Solution:** Migrate to Prometheus with PromQL support, maintaining backward compatibility through dual-write and gradual adoption phases.

**Timeline:** 10 weeks (phased rollout over 5 sprints)

## Table of Contents

1. [Current Architecture](#current-architecture)
2. [Proposed Architecture](#proposed-architecture-options)
3. [Implementation Phases](#implementation-phases)
4. [Technical Design](#technical-design-details)
5. [Testing Strategy](#testing-strategy)
6. [Success Criteria](#success-criteria)
7. [Open Questions](#open-questions-for-feedback)

## Current Architecture

### Metrics Data Flow

```
Application (OTel SDK)
  ↓ OTLP/gRPC (4317) or OTLP/HTTP (4318)
OTel Collector
  ↓ spanmetrics connector generates RED metrics
  ↓ batch processor
  ↓ OTLP exporter (4343)
TinyOlly OTLP Receiver
  ↓ parse_otlp_metrics() in storage.py
  ↓ compress with ZSTD + msgpack
  ↓ store in Redis sorted sets
Redis (6379)
  ↓ Keys: metrics:names, metrics:series:{name}:{hash}, etc.
  ↓ 30-minute TTL (automatic cleanup)
TinyOlly REST API
  ↓ /api/metrics → retrieves from Redis
  ↓ Returns JSON with all series data
Browser (metrics.js)
  ↓ Receives complete dataset
  ↓ Client-side filtering, aggregation
  ↓ Chart.js rendering
```

### Performance Characteristics

| Aspect | Current (Redis) | Bottleneck |
|--------|-----------------|------------|
| **Write Performance** | Excellent (O(log N)) | ✅ Good |
| **Storage Efficiency** | Good (ZSTD+msgpack) | ✅ Good |
| **Query Performance** | Good (<100 series) | ⚠️ Degrades with cardinality |
| **UI Responsiveness** | Fast (<1000 series) | ❌ Slow with >1000 series |
| **Aggregation** | Client-side only | ❌ All in browser |
| **Query Language** | None | ❌ Limited capabilities |
| **Retention** | 30 minutes (fixed) | ⚠️ No historical data |
| **Cardinality Limit** | 1000 metric names | ⚠️ Arbitrary limit |

### Code Locations

- **Storage:** `apps/tinyolly/common/storage.py` (lines 743-1253)
- **API:** `apps/tinyolly/app/routers/query.py` (lines 237-350)
- **UI:** `apps/tinyolly-ui/src/modules/metrics.js`
- **Tests:** `apps/tinyolly/tests/test_metrics.py`

## Proposed Architecture Options

### Option A: Prometheus Standalone (Recommended)

**Best for:** Production use, Kubernetes deployments

```
OTel Collector → prometheusremotewrite exporter → Prometheus (9090)
TinyOlly API → HTTP proxy → Prometheus (/api/v1/query)
Browser → PromQL queries → Server-side aggregation → Rendered results
```

**Configuration:**
```yaml
prometheus:
  mode: standalone
  retention: 2h  # Desktop default
  persistence: false  # Memory-only for dev
  resources:
    memory: 200-400 MB
    cpu: 10-20%
```

**Pros:**
- Full Prometheus capabilities
- Grafana integration works
- Production-ready patterns
- Can scale to long retention

**Cons:**
- More resources than Redis
- Requires persistent storage for production
- Additional container to manage

### Option B: Prometheus Agent Mode (Lightweight)

**Best for:** Desktop development, resource-constrained environments

```
OTel Collector → Prometheus Agent (embedded/sidecar)
  → Memory-only storage (no disk)
  → Optional: forward to remote Prometheus
TinyOlly API → Query local agent
```

**Configuration:**
```yaml
prometheus:
  mode: agent
  retention: 1h  # Memory-only
  persistence: false
  resources:
    memory: 100-200 MB
    cpu: 5-10%
  remoteWrite:
    enabled: false  # Optional for production
```

**Pros:**
- Lightweight (~half the resources)
- No disk usage
- Still supports PromQL
- Can forward to production Prometheus

**Cons:**
- Limited retention (memory-only)
- Less suitable for production
- Requires remote_write for history

### Option C: Dual-Write (Transition Phase)

**Best for:** Migration period

```
OTel Collector
  ├─→ Prometheus Remote Write (new path)
  └─→ OTLP to TinyOlly → Redis (legacy path)

TinyOlly API
  ├─→ Try Prometheus (if available)
  └─→ Fallback to Redis (if Prometheus down)
```

**Configuration:**
```bash
METRICS_BACKEND=auto  # Try Prometheus, fall back to Redis
# METRICS_BACKEND=prometheus  # Prometheus only (fail if down)
# METRICS_BACKEND=redis  # Legacy mode
```

**Pros:**
- Zero-downtime migration
- Validates consistency
- Backward compatibility
- Rollback safety

**Cons:**
- Double storage overhead
- More complex configuration
- Temporary state

### Recommendation

**Phase 1-3:** Option C (Dual-write during migration)  
**Phase 4+:** Option B by default (agent mode), Option A for production  
**Long-term:** Option A becomes default in TinyOlly 3.0

## Implementation Phases

### Phase 1: Prometheus Deployment (Weeks 1-2)

**Goal:** Deploy Prometheus alongside Redis, validate dual-write

**Tasks:**

1. **Docker Deployment**
   - [ ] Create `docker/docker-compose.prometheus.yml`
   - [ ] Add Prometheus configuration in `config/prometheus/prometheus.yml`
   - [ ] Update startup scripts to optionally include Prometheus

2. **Kubernetes Deployment**
   - [ ] Add Prometheus to Helm chart `charts/tinyolly/templates/prometheus.yaml`
   - [ ] Configure values.yaml with prometheus section
   - [ ] Add HTTPRoute for Prometheus UI (optional)

3. **OTel Collector Configuration**
   - [ ] Add `prometheusremotewrite` exporter to config
   - [ ] Configure dual-write pipeline (OTLP + Prometheus)
   - [ ] Add resource_to_telemetry_conversion

4. **Validation**
   - [ ] Verify metrics appear in Prometheus UI (localhost:9090)
   - [ ] Compare data between Redis and Prometheus
   - [ ] Benchmark resource usage

**Deliverables:**
- Docker compose file with Prometheus
- Helm chart updates
- OTel Collector config with dual-write
- Setup documentation

**Success Criteria:**
- ✅ Prometheus receives metrics via remote write
- ✅ Data matches between Redis and Prometheus
- ✅ Resource usage acceptable (<500 MB total)

### Phase 2: PromQL API Proxy (Weeks 3-4)

**Goal:** Expose Prometheus via TinyOlly REST API

**Tasks:**

1. **Create PromQL Router**
   - [ ] New file: `apps/tinyolly/app/routers/promql.py`
   - [ ] Implement `/api/promql/query` (instant query)
   - [ ] Implement `/api/promql/query_range` (range query)
   - [ ] Implement `/api/promql/label/{label}/values`
   - [ ] Implement `/api/promql/series` (metadata)

2. **Backend Selection Logic**
   - [ ] Add `METRICS_BACKEND` environment variable
   - [ ] Update `/api/metrics` endpoints with backend selection
   - [ ] Implement Prometheus → TinyOlly format conversion
   - [ ] Implement OTel → Prometheus name conversion

3. **Error Handling**
   - [ ] Graceful fallback from Prometheus to Redis
   - [ ] Clear error messages when Prometheus unavailable
   - [ ] Timeout handling for slow queries

4. **Testing**
   - [ ] Unit tests for name conversion
   - [ ] Integration tests for PromQL endpoints
   - [ ] Test backend fallback logic

**Deliverables:**
- PromQL router with 5 endpoints
- Backend selection middleware
- Name conversion utilities
- OpenAPI documentation updates

**Success Criteria:**
- ✅ PromQL queries return correct data
- ✅ Backend fallback works seamlessly
- ✅ Backward compatibility maintained
- ✅ API response time <1 second

### Phase 3: Frontend PromQL Integration (Weeks 5-7)

**Goal:** Refactor UI to use PromQL queries

**Tasks:**

1. **PromQL Query Module**
   - [ ] Create `apps/tinyolly-ui/src/modules/promql.js`
   - [ ] Implement PromQL query builder
   - [ ] Add query templates for common operations

2. **Update Metrics Rendering**
   - [ ] Modify `renderMetricChart()` to detect backend
   - [ ] Implement PromQL-based chart rendering
   - [ ] Update cardinality explorer to use `/api/v1/series`
   - [ ] Add "View Query" button showing actual PromQL

3. **Update Filters**
   - [ ] Generate PromQL label selectors from UI filters
   - [ ] Update metric search to work with both backends
   - [ ] Preserve exemplar trace linking

4. **Update Service Catalog**
   - [ ] Rewrite RED metrics calculation using PromQL:
     - Rate: `sum(rate(http_server_duration_count[5m]))`
     - Errors: `sum(rate(http_server_duration_count{status_code=~"5.."}[5m]))`
     - Duration: `histogram_quantile(0.95, ...)`

5. **Performance Optimizations**
   - [ ] Server-side aggregation instead of client-side
   - [ ] Lazy loading for high-cardinality metrics
   - [ ] Pagination for series list

**Deliverables:**
- Updated metrics.js with PromQL support
- New promql.js module
- Updated service catalog with PromQL queries
- Performance benchmark results

**Success Criteria:**
- ✅ Metrics page works with Prometheus backend
- ✅ 2x performance improvement for >1000 series
- ✅ All features preserved (charts, filters, exemplars)
- ✅ UI responsive with 10k+ series

### Phase 4: Documentation & Polish (Week 8)

**Goal:** Complete user-facing documentation

**Tasks:**

1. **Setup Guides**
   - [ ] Update `docs/quickstart.md` with Prometheus option
   - [ ] Create `docs/prometheus-setup.md`
   - [ ] Add troubleshooting guide

2. **PromQL Documentation**
   - [ ] Create `docs/promql-examples.md` with common queries
   - [ ] Document query templates
   - [ ] Add Grafana integration guide

3. **Migration Guide**
   - [ ] Create `docs/migration/prometheus.md`
   - [ ] Document configuration options
   - [ ] Add FAQ section

4. **Architecture Documentation**
   - [ ] Update architecture diagrams
   - [ ] Document data flow
   - [ ] Add resource requirements table

**Deliverables:**
- Complete documentation set
- Grafana dashboard examples
- Migration checklist

**Success Criteria:**
- ✅ Clear setup instructions for Docker and Kubernetes
- ✅ PromQL examples cover common use cases
- ✅ Migration path clear for existing users

### Phase 5: Default to Prometheus (Week 9-10)

**Goal:** Make Prometheus the default backend (optional)

**Tasks:**

1. **Update Defaults**
   - [ ] Change default `METRICS_BACKEND=prometheus` in code
   - [ ] Update docker-compose to include Prometheus by default
   - [ ] Update Helm chart with `prometheus.enabled=true`

2. **Deprecation Notices**
   - [ ] Add deprecation warning for Redis metrics in logs
   - [ ] Update documentation with timeline
   - [ ] Add migration guide link to UI

3. **Beta Testing**
   - [ ] Deploy to test environment
   - [ ] Gather user feedback
   - [ ] Address issues

4. **Release**
   - [ ] Release notes highlighting Prometheus
   - [ ] Blog post or demo video
   - [ ] Announcement in community channels

**Deliverables:**
- TinyOlly 2.x release with Prometheus default
- Release announcement
- Community feedback

**Success Criteria:**
- ✅ New installs use Prometheus by default
- ✅ Existing installs can opt-in
- ✅ No major regressions reported

## Technical Design Details

### OTel ↔ Prometheus Metric Name Conversion

**Challenge:** OpenTelemetry uses dots (`.`), Prometheus uses underscores (`_`)

**Solution:**

```python
def otel_to_prometheus_name(otel_name: str, unit: str = "") -> str:
    """
    Convert OTel metric name to Prometheus naming convention.
    
    Rules:
    1. Replace dots with underscores
    2. Add unit suffix (Prometheus best practice)
    3. Handle counter _total suffix
    
    Examples:
        http.server.duration (ms) → http_server_duration_milliseconds
        http.server.request.size (By) → http_server_request_size_bytes
        http.server.request.count (1) → http_server_request_count_total
    """
    # Step 1: Replace dots with underscores
    prom_name = otel_name.replace(".", "_")
    
    # Step 2: Add unit suffix
    unit_suffixes = {
        "ms": "_milliseconds",
        "s": "_seconds",
        "By": "_bytes",
        "1": "",  # Dimensionless
        "%": "_percent"
    }
    
    if unit in unit_suffixes and unit_suffixes[unit]:
        suffix = unit_suffixes[unit]
        # Don't duplicate if already present
        if not prom_name.endswith(suffix.replace("_", "")):
            prom_name += suffix
    
    # Step 3: Counter total suffix (based on metric type)
    # This requires metadata lookup - simplified for now
    if "count" in prom_name and not prom_name.endswith("_total"):
        prom_name += "_total"
    
    return prom_name

def prometheus_to_otel_name(prom_name: str) -> str:
    """
    Convert Prometheus metric name back to OTel format.
    
    Removes unit suffixes and converts underscores to dots.
    """
    # Remove common suffixes
    suffixes = ["_milliseconds", "_seconds", "_bytes", "_total", "_percent", "_ratio"]
    for suffix in suffixes:
        if prom_name.endswith(suffix):
            prom_name = prom_name[:-len(suffix)]
            break
    
    # Convert underscores to dots
    otel_name = prom_name.replace("_", ".")
    
    return otel_name
```

### PromQL Query Templates

**Service RED Metrics:**

```python
RED_METRIC_TEMPLATES = {
    "rate": """
        sum(rate({metric_name}_count{{service_name="{service}"}}[{interval}]))
    """,
    
    "error_rate": """
        sum(rate({metric_name}_count{{service_name="{service}",status_code=~"5.."}}[{interval}])) /
        sum(rate({metric_name}_count{{service_name="{service}"}}[{interval}]))
    """,
    
    "duration_p50": """
        histogram_quantile(0.50,
          sum(rate({metric_name}_bucket{{service_name="{service}"}}[{interval}])) by (le)
        )
    """,
    
    "duration_p95": """
        histogram_quantile(0.95,
          sum(rate({metric_name}_bucket{{service_name="{service}"}}[{interval}])) by (le)
        )
    """,
    
    "duration_p99": """
        histogram_quantile(0.99,
          sum(rate({metric_name}_bucket{{service_name="{service}"}}[{interval}])) by (le)
        )
    """
}

def build_service_red_query(service_name: str, interval: str = "5m") -> dict:
    """Build PromQL queries for service RED metrics"""
    metric_name = "http_server_duration"  # OTel standard
    
    return {
        key: template.format(
            metric_name=metric_name,
            service=service_name,
            interval=interval
        ).strip()
        for key, template in RED_METRIC_TEMPLATES.items()
    }
```

**Cardinality Analysis:**

```python
CARDINALITY_QUERIES = {
    "label_values": """
        label_values({metric_name}, {label_name})
    """,
    
    "series_count": """
        count({metric_name})
    """,
    
    "series_by_label": """
        count by ({label_name}) ({metric_name})
    """,
    
    "high_cardinality_labels": """
        count by (__name__) (
          count by (__name__, {label_name}) ({metric_name})
        )
    """
}
```

### API Response Format Conversion

**Prometheus Format:**

```json
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "http_server_duration_milliseconds",
          "service_name": "api",
          "http_method": "GET"
        },
        "values": [
          [1705343400, "123.45"],
          [1705343415, "125.67"]
        ]
      }
    ]
  }
}
```

**TinyOlly Format:**

```json
{
  "name": "http.server.duration",
  "type": "histogram",
  "unit": "ms",
  "description": "HTTP server duration",
  "backend": "prometheus",
  "series": [
    {
      "resource": {
        "service.name": "api"
      },
      "attributes": {
        "http.method": "GET"
      },
      "datapoints": [
        {"timestamp": 1705343400.0, "value": 123.45},
        {"timestamp": 1705343415.0, "value": 125.67}
      ],
      "exemplars": []
    }
  ]
}
```

**Conversion Function:**

```python
def convert_prometheus_to_tinyolly(name: str, prom_response: dict) -> dict:
    """Convert Prometheus API response to TinyOlly MetricDetail format"""
    data = prom_response.get("data", {})
    results = data.get("result", [])
    
    series = []
    for result in results:
        labels = result.get("metric", {})
        values = result.get("values", [])
        
        # Separate resource vs metric attributes
        resource = {}
        attributes = {}
        
        for key, value in labels.items():
            if key == "__name__":
                continue
            
            # Resource attributes: service.*, host.*, deployment.*
            if key.startswith(("service_", "host_", "deployment_", "container_")):
                # Convert prometheus_naming to otel.naming
                otel_key = key.replace("_", ".")
                resource[otel_key] = value
            else:
                # Metric labels
                attributes[key] = value
        
        # Convert timestamp, value pairs
        datapoints = [
            {
                "timestamp": float(ts),
                "value": float(val)
            }
            for ts, val in values
        ]
        
        series.append({
            "resource": resource,
            "attributes": attributes,
            "datapoints": datapoints,
            "exemplars": []  # TODO: Extract exemplars if present
        })
    
    return {
        "name": name,
        "type": "unknown",  # Prometheus doesn't expose type easily
        "unit": "",
        "description": "",
        "backend": "prometheus",
        "series": series
    }
```

### Configuration Management

**Environment Variables:**

```bash
# Backend selection
METRICS_BACKEND=auto          # Try Prometheus, fall back to Redis (default)
# METRICS_BACKEND=prometheus  # Prometheus only (fail if unavailable)
# METRICS_BACKEND=redis       # Redis only (legacy mode)

# Prometheus connection
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_TIMEOUT=30s
PROMETHEUS_QUERY_MAX_SAMPLES=50000000  # Default: 50M samples

# Redis connection (fallback)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_TTL=1800  # 30 minutes
```

**Helm Chart Values:**

```yaml
# values.yaml
metrics:
  # Backend selection
  backend: "auto"  # auto | prometheus | redis
  
  # Prometheus configuration
  prometheus:
    enabled: true
    mode: "agent"  # agent | standalone
    
    image:
      repository: prom/prometheus
      tag: v2.51.0
      pullPolicy: IfNotPresent
    
    # Retention configuration
    retention: "2h"  # For desktop use
    retentionSize: ""  # e.g., "1GB"
    
    # Resource limits
    resources:
      requests:
        memory: "128Mi"
        cpu: "50m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    
    # Storage
    persistence:
      enabled: false  # Memory-only for desktop
      size: "10Gi"
      storageClass: ""
      accessMode: ReadWriteOnce
    
    # Remote write (optional)
    remoteWrite:
      enabled: false
      url: ""
      # OAuth2 or basic auth
      basicAuth:
        username: ""
        passwordSecret: ""
      oauth2:
        enabled: false
        clientId: ""
        clientSecretSecret: ""
        tokenUrl: ""
    
    # Prometheus config
    config:
      scrapeInterval: "15s"
      evaluationInterval: "15s"
      # Additional scrape configs
      scrapeConfigs: []
    
    # Service configuration
    service:
      type: ClusterIP
      port: 9090
    
    # Ingress (optional, for Prometheus UI)
    ingress:
      enabled: false
      className: "envoy-gateway"
      host: "prometheus.tinyolly.test"
  
  # Redis configuration (legacy/fallback)
  redis:
    enabled: true
    host: "tinyolly-redis"
    port: 6379
    ttl: 1800  # 30 minutes
```

## Testing Strategy

### Unit Tests

```python
# Test name conversion
def test_otel_to_prometheus_name():
    assert otel_to_prometheus_name("http.server.duration", "ms") == \
           "http_server_duration_milliseconds"
    assert otel_to_prometheus_name("process.cpu.utilization", "1") == \
           "process_cpu_utilization"
    assert otel_to_prometheus_name("http.server.request.count", "1") == \
           "http_server_request_count_total"

def test_prometheus_to_otel_name():
    assert prometheus_to_otel_name("http_server_duration_milliseconds") == \
           "http.server.duration"
    assert prometheus_to_otel_name("http_server_request_count_total") == \
           "http.server.request.count"

# Test PromQL query builder
def test_build_promql_query():
    query = build_promql_query(
        "http.server.duration",
        {"service": "api", "http.method": "GET"},
        interval="5m"
    )
    expected = 'rate(http_server_duration_milliseconds{service="api",http_method="GET"}[5m])'
    assert query == expected

# Test format conversion
def test_convert_prometheus_to_tinyolly():
    prom_response = {
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {
                        "__name__": "http_server_duration_milliseconds",
                        "service_name": "api",
                        "http_method": "GET"
                    },
                    "values": [
                        [1000, "123"],
                        [1015, "125"]
                    ]
                }
            ]
        }
    }
    
    result = convert_prometheus_to_tinyolly("http.server.duration", prom_response)
    
    assert result["name"] == "http.server.duration"
    assert result["backend"] == "prometheus"
    assert len(result["series"]) == 1
    assert len(result["series"][0]["datapoints"]) == 2
    assert result["series"][0]["resource"]["service.name"] == "api"
    assert result["series"][0]["attributes"]["http.method"] == "GET"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_dual_write_consistency():
    """Verify metrics written to both backends match"""
    # Send test metrics
    await send_test_metrics_otlp({
        "name": "test.counter",
        "value": 42,
        "attributes": {"service": "test"}
    })
    
    # Wait for ingestion
    await asyncio.sleep(2)
    
    # Query from Prometheus
    prom_data = await query_prometheus("test_counter_total")
    
    # Query from Redis
    redis_data = await storage.get_metric_series("test.counter")
    
    # Compare
    assert len(prom_data["series"]) == len(redis_data)
    assert prom_data["series"][0]["datapoints"][0]["value"] == \
           redis_data[0]["datapoints"][0]["value"]

@pytest.mark.asyncio
async def test_backend_fallback():
    """Test fallback from Prometheus to Redis when Prometheus unavailable"""
    # Stop Prometheus
    await stop_prometheus_container()
    
    # Query should still work via Redis
    response = await client.get("/api/metrics/http.server.duration")
    
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "redis"
    
    # Restart Prometheus
    await start_prometheus_container()

@pytest.mark.asyncio
async def test_promql_proxy_endpoints():
    """Test PromQL proxy endpoints"""
    # Instant query
    response = await client.get(
        "/api/promql/query",
        params={"query": "up"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Range query
    response = await client.get(
        "/api/promql/query_range",
        params={
            "query": "rate(http_server_duration_count[5m])",
            "start": time.time() - 600,
            "end": time.time(),
            "step": "15s"
        }
    )
    assert response.status_code == 200
    
    # Label values
    response = await client.get("/api/promql/label/service_name/values")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

### Performance Benchmarks

```python
@pytest.mark.benchmark
async def test_query_performance_high_cardinality():
    """Compare query performance with high cardinality"""
    # Setup: Ingest 10k unique series
    await ingest_high_cardinality_metrics(series_count=10000)
    
    # Benchmark Redis
    start = time.time()
    redis_result = await storage.get_metric_series(
        "http.server.duration",
        attr_filter={"service": "api"}
    )
    redis_duration = time.time() - start
    
    # Benchmark Prometheus
    start = time.time()
    prom_result = await query_prometheus(
        'http_server_duration_milliseconds{service="api"}'
    )
    prom_duration = time.time() - start
    
    # Prometheus should be faster
    assert prom_duration < redis_duration
    assert prom_duration < 1.0  # Sub-second query
    
    print(f"Redis: {redis_duration:.3f}s, Prometheus: {prom_duration:.3f}s")
    print(f"Speedup: {redis_duration / prom_duration:.2f}x")

@pytest.mark.benchmark
async def test_ui_rendering_performance():
    """Test UI rendering with high cardinality"""
    # Setup: 10k series
    await ingest_high_cardinality_metrics(series_count=10000)
    
    # Measure page load time
    start = time.time()
    
    # Load metrics page
    await browser.goto("http://localhost:5005")
    await browser.wait_for_selector("#metrics-container")
    
    load_duration = time.time() - start
    
    # Should load in <2 seconds with Prometheus
    assert load_duration < 2.0
    
    print(f"Page load: {load_duration:.3f}s")
```

### End-to-End Tests

```python
@pytest.mark.e2e
async def test_complete_metrics_flow():
    """Test complete flow from ingestion to visualization"""
    # 1. Send metrics via OTLP
    await send_otlp_metrics({
        "name": "test.histogram",
        "type": "histogram",
        "unit": "ms",
        "datapoints": [
            {"value": 100, "timestamp": time.time()},
            {"value": 200, "timestamp": time.time()}
        ],
        "attributes": {"service": "test-app"}
    })
    
    # 2. Wait for ingestion
    await asyncio.sleep(2)
    
    # 3. Verify in Prometheus
    prom_result = await query_prometheus('test_histogram_milliseconds_bucket')
    assert len(prom_result["data"]["result"]) > 0
    
    # 4. Query via TinyOlly API
    api_result = await client.get("/api/metrics/test.histogram")
    assert api_result.status_code == 200
    assert api_result.json()["backend"] == "prometheus"
    
    # 5. Verify UI displays correctly
    await browser.goto("http://localhost:5005")
    await browser.click('text="Metrics"')
    await browser.fill("#metric-search", "test.histogram")
    
    # Should see metric in table
    metric_row = await browser.query_selector('[data-metric-name="test.histogram"]')
    assert metric_row is not None
    
    # Click to view chart
    await browser.click('[data-metric-name="test.histogram"] button')
    
    # Should render chart
    chart = await browser.query_selector("canvas")
    assert chart is not None
```

## Success Criteria

### Functional Requirements

| ID | Requirement | Target | Measured By |
|----|-------------|--------|-------------|
| F1 | Metrics page displays correctly | ✅ Pass | Manual testing |
| F2 | PromQL queries return accurate data | ✅ Pass | Integration tests |
| F3 | Cardinality explorer shows correct analysis | ✅ Pass | E2E tests |
| F4 | Service catalog RED metrics work | ✅ Pass | API tests |
| F5 | Exemplar trace linking preserved | ✅ Pass | UI tests |
| F6 | Backward compatibility maintained | ✅ Pass | Regression tests |
| F7 | Backend selection works (auto/prom/redis) | ✅ Pass | Config tests |
| F8 | Grafana can query TinyOlly Prometheus | ✅ Pass | Integration guide |

### Performance Requirements

| ID | Requirement | Target | Current (Redis) | Measured By |
|----|-------------|--------|-----------------|-------------|
| P1 | Metrics page load (high cardinality) | <2s | 5-10s | Benchmark |
| P2 | PromQL query completion | <1s | N/A | Benchmark |
| P3 | UI responsiveness (10k+ series) | Smooth | Laggy | Manual testing |
| P4 | Prometheus memory overhead | <500MB | ~100MB (Redis) | Monitoring |
| P5 | No impact on trace/log performance | Same | Same | Benchmark |

### User Experience Requirements

| ID | Requirement | Success Criteria |
|----|-------------|------------------|
| U1 | Zero-config preserved | Docker compose works without Prometheus flag |
| U2 | Clear Prometheus setup docs | <5 minutes to enable Prometheus |
| U3 | "View Query" shows PromQL | Button visible in metrics detail |
| U4 | Helpful error messages | Clear guidance when Prometheus down |
| U5 | Migration guide available | Existing users can upgrade smoothly |

## Open Questions for Feedback

### 1. Default Backend

**Question:** Should Prometheus be enabled by default in new installs?

**Options:**
- **A:** Disabled (opt-in) - maintains zero-config experience
- **B:** Enabled (opt-out) - pushes production-ready patterns

**Considerations:**
- **Pro (opt-in):** Maintains simplicity, lower resource usage
- **Pro (opt-out):** Modern default, better developer experience
- **Con (opt-in):** Extra setup step
- **Con (opt-out):** More resources, complexity

**Recommendation:** Option A for v2.x, Option B for v3.0

**Vote:** 👍 A | 👎 B | 💬 Comment

---

### 2. Prometheus Mode

**Question:** Which Prometheus mode for desktop development?

**Options:**
- **A:** Agent mode (memory-only, 100-200 MB)
- **B:** Standalone mode (disk storage, 200-400 MB)
- **C:** User configurable (default agent, option standalone)

**Recommendation:** Option C (agent by default, configurable)

**Vote:** 👍 C | 👎 A/B | 💬 Comment

---

### 3. Dual-Write Duration

**Question:** How long should dual-write be maintained?

**Options:**
- **A:** 1 release (~1 month)
- **B:** 2 releases (~2 months)
- **C:** Until Redis metrics deprecated (6+ months)

**Recommendation:** Option B (2 releases)

**Vote:** 👍 B | 👎 A/C | 💬 Comment

---

### 4. Scope Expansion

**Question:** Should we also migrate traces and logs to specialized backends?

**Traces:** Tempo, Jaeger  
**Logs:** Loki

**Considerations:**
- **Pro:** Consistent approach, production patterns
- **Con:** Significant complexity increase

**Recommendation:** Metrics only for now, evaluate later

**Vote:** 👍 Metrics only | 👎 Include traces/logs | 💬 Comment

---

### 5. Redis Deprecation

**Question:** Should Redis metrics eventually be removed?

**Options:**
- **A:** Keep indefinitely (legacy option)
- **B:** Deprecate in v3.0, remove in v4.0
- **C:** Keep for dev, Prometheus for production

**Recommendation:** Option C (hybrid approach)

**Vote:** 👍 C | 👎 A/B | 💬 Comment

## Timeline & Resource Allocation

### Sprint Plan

| Sprint | Week | Phase | Effort | Deliverables |
|--------|------|-------|--------|--------------|
| Sprint 1 | 1-2 | Phase 1: Prometheus Deployment | 3 days | Docker/K8s configs, dual-write |
| Sprint 2 | 3-4 | Phase 2: PromQL API Proxy | 5 days | API endpoints, backend selection |
| Sprint 3 | 5-6 | Phase 3a: Frontend PromQL (Part 1) | 5 days | Query module, chart rendering |
| Sprint 4 | 7 | Phase 3b: Frontend PromQL (Part 2) | 3 days | Service catalog, cardinality |
| Sprint 5 | 8-9 | Phase 4: Docs + Phase 5: Default | 4 days | Documentation, rollout |

**Total Duration:** 9 weeks (20 working days)

### Resource Requirements

**Development:**
- 1 Backend Developer (Python/FastAPI) - 60% allocation
- 1 Frontend Developer (JavaScript) - 40% allocation
- 1 DevOps Engineer (Docker/Kubernetes) - 20% allocation

**Infrastructure:**
- CI/CD pipeline for integration tests
- Performance testing environment
- Staging environment for beta testing

**Documentation:**
- Technical writer for user guides (10 hours)
- Video creator for demo (5 hours)

## Risk Analysis & Mitigation

### High Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Prometheus adds too much complexity | High | Medium | Make optional, provide clear docs, use agent mode |
| Breaking changes for users | High | Medium | Dual-write, feature flags, migration guide |
| Performance not as expected | High | Low | Early benchmarks, iterative tuning |

### Medium Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Resource overhead on dev machines | Medium | Medium | Use lightweight agent mode, configurable retention |
| OTel ↔ Prometheus naming issues | Medium | High | Comprehensive tests, edge case handling, docs |
| User adoption resistance | Medium | Low | Clear benefits, smooth migration path |

### Low Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| UI rendering regressions | Low | Low | Extensive testing, format conversion layer |
| Loss of exemplar support | Low | Low | Preserve in conversion, test thoroughly |
| Documentation gaps | Low | Medium | Comprehensive docs, community feedback |

## Next Steps

1. **Review & Approve This Plan**
   - Gather feedback on architecture approach
   - Vote on open questions
   - Identify concerns or blockers

2. **Create GitHub Issues**
   - Break down phases into implementable issues
   - Assign to team members
   - Set milestones

3. **Begin Phase 1**
   - Start with Prometheus deployment
   - Validate dual-write approach
   - Measure performance

4. **Regular Progress Updates**
   - Weekly status updates
   - Demo sessions after each phase
   - Gather user feedback early

5. **Documentation First**
   - Write setup guides as we build
   - Create troubleshooting docs
   - Prepare migration resources

## Conclusion

This migration to Prometheus represents a significant architectural improvement for TinyOlly, addressing performance issues while enabling production-ready patterns. The phased approach ensures backward compatibility, reduces risk, and allows for iterative feedback.

**Key Benefits:**
- 🚀 Improved performance for high-cardinality metrics
- 📊 Production-ready PromQL query language
- 🔗 Grafana integration for advanced dashboards
- 📈 Path to production observability patterns

**Key Challenges:**
- 📦 Additional service to deploy
- 💾 Higher resource usage
- 🔧 More configuration options

**Recommendation:** Proceed with phased implementation, starting with Phase 1 deployment and validation.

---

**Questions or Feedback?** 
- Comment on this document
- Open a GitHub Discussion
- Join the community Slack/Discord

**Document Version:** 1.0  
**Last Updated:** 2026-01-15  
**Status:** Awaiting Feedback
