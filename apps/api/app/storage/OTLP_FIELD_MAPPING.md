w# OTLP Field Mapping Documentation

## Protobuf to Dict Conversion

When using `MessageToDict(proto_obj, preserving_proto_field_name=True)`:

- Field names use **snake_case** (not camelCase)
- This matches the protobuf field definition names exactly

## OTLP Structure (from protobuf with preserving_proto_field_name=True)

### Traces

```text
resource_spans: []
  ├─ resource: { attributes: [] }
  └─ scope_spans: []
      ├─ scope: {}
      └─ spans: []
```

### Logs

```text
resource_logs: []
  ├─ resource: { attributes: [] }
  └─ scope_logs: []
      ├─ scope: {}
      └─ log_records: []
```

### Metrics

```text
resource_metrics: []
  ├─ resource: { attributes: [] }
  └─ scope_metrics: []
      ├─ scope: {}
      └─ metrics: []
          └─ [gauge|sum|histogram|summary]: { data_points: [] }
```

## Database Model Mapping (apps/frontend/app/models/database.py)

### logs_fact

- tenant_id: int (FK tenant_dim.id)
- connection_id: int (FK connection_dim.id)
- trace_id: str | None (max 32, hex)
- span_id: str | None (max 16, hex)
- timestamp: datetime (from time_unix_nano)
- nanos_fraction: int (0-999, from time_unix_nano)
- observed_timestamp: datetime | None (from observed_time_unix_nano)
- observed_nanos_fraction: int (0-999, from observed_time_unix_nano)
- severity_number: int | None
- severity_text: str | None (max 64)
- body: dict | None (JSONB)
- service_id: int | None (FK service_dim.id)
- attributes: dict | None (JSONB)
- resource: dict | None (JSONB)
- scope: dict | None (JSONB)
- flags: int (default 0)
- dropped_attributes_count: int (default 0)
- created_at: datetime (auto)

### spans_fact

- tenant_id: int (FK tenant_dim.id)
- connection_id: int (FK connection_dim.id)
- trace_id: str (max 32, hex, required)
- span_id: str (max 16, hex, required)
- parent_span_id: str | None (max 16, hex)
- name: str (max 1024, required)
- kind: int (0-5, required)
- status_code: int | None
- status_message: str | None (text)
- start_timestamp: datetime (from start_time_unix_nano)
- start_nanos_fraction: int (0-999)
- end_timestamp: datetime (from end_time_unix_nano)
- end_nanos_fraction: int (0-999)
- service_id: int | None (FK service_dim.id)
- operation_id: int | None (FK operation_dim.id)
- resource_id: int | None (FK resource_dim.id)
- attributes: dict | None (JSONB)
- events: dict | None (JSONB)
- links: dict | None (JSONB)
- resource: dict | None (JSONB)
- scope: dict | None (JSONB)
- flags: int (default 0)
- dropped_attributes_count: int (default 0)
- dropped_events_count: int (default 0)
- dropped_links_count: int (default 0)
- created_at: datetime (auto)

### metrics_fact

- tenant_id: int (FK tenant_dim.id)
- connection_id: int (FK connection_dim.id)
- timestamp: datetime (from time_unix_nano)
- nanos_fraction: int (0-999)
- start_timestamp: datetime | None (from start_time_unix_nano)
- start_nanos_fraction: int (0-999)
- metric_name: str (max 1024, required)
- metric_type: str (max 32, required: "gauge", "sum", "histogram", "summary")
- unit: str | None (max 64)
- description: str | None (text)
- service_id: int | None (FK service_dim.id)
- resource: dict | None (JSONB)
- scope: dict | None (JSONB)
- attributes: dict | None (JSONB) - data point attributes
- data_points: dict | None (JSONB) - ALL data points for this metric
- temporality: str | None (max 32)
- is_monotonic: bool | None
- created_at: datetime (auto)
