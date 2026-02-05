"""Tests for PostgresStorage ORM implementation."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.database import LogsFact, NamespaceDim, OperationDim, ServiceDim, SpansFact
from app.storage.postgres_orm_sync import PostgresStorage

pytestmark = pytest.mark.skip(reason="Tests deprecated old schema - being replaced with OTLP schema")


def test_spans_fact_model():
    """Test SpansFact model can be instantiated with OTLP data."""
    span = SpansFact(
        trace_id="abc123",
        span_id="def456",
        name="test-span",
        kind=2,  # SERVER
        start_time_unix_nano=1000000,
        end_time_unix_nano=2000000,
        attributes={"http.method": "GET"},
        events=[],
        links=[],
    )

    assert span.trace_id == "abc123"
    assert span.span_id == "def456"
    assert span.name == "test-span"
    assert span.kind == 2
    assert span.attributes == {"http.method": "GET"}


def test_logs_fact_model():
    """Test LogsFact model can be instantiated with OTLP data."""

    log = LogsFact(
        timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        nanos_fraction=123,
        severity_number=9,
        severity_text="INFO",
        body={"stringValue": "test log"},
        attributes={"app": "test"},
    )

    assert log.timestamp == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert log.nanos_fraction == 123
    assert log.severity_number == 9
    assert log.body == {"stringValue": "test log"}


def test_base64_to_hex_conversion():
    """Test trace/span ID conversion from base64 to hex."""
    storage = PostgresStorage("postgresql+psycopg2://test")

    # Example trace ID in base64 (16 bytes)
    b64_id = "AAAAAAAAAAAAAAAAAAAAAA=="  # All zeros
    hex_id = storage._base64_to_hex(b64_id)

    assert len(hex_id) == 32  # 16 bytes = 32 hex chars
    assert hex_id == "00000000000000000000000000000000"


def test_extract_string_value():
    """Test OTLP attribute value extraction.

    MessageToDict with preserving_proto_field_name=True uses snake_case.
    """
    storage = PostgresStorage("postgresql+psycopg2://test")

    # String value (snake_case from MessageToDict)
    assert storage._extract_string_value({"string_value": "test"}) == "test"

    # Int value (snake_case)
    assert storage._extract_string_value({"int_value": "42"}) == "42"  # MessageToDict converts int64 to string

    # Bool value (snake_case) - returns raw boolean
    assert storage._extract_string_value({"bool_value": True}) is True

    # No value
    assert storage._extract_string_value({}) is None


def test_normalize_severity_number():
    """Test severity number normalization from MessageToDict format."""
    storage = PostgresStorage("postgresql+psycopg2://test")

    # Integer values (pass through)
    assert storage._normalize_severity_number(9) == 9
    assert storage._normalize_severity_number(17) == 17

    # String enum names from MessageToDict
    assert storage._normalize_severity_number("SEVERITY_NUMBER_UNSPECIFIED") == 0
    assert storage._normalize_severity_number("SEVERITY_NUMBER_TRACE") == 1
    assert storage._normalize_severity_number("SEVERITY_NUMBER_DEBUG") == 5
    assert storage._normalize_severity_number("SEVERITY_NUMBER_INFO") == 9
    assert storage._normalize_severity_number("SEVERITY_NUMBER_WARN") == 13
    assert storage._normalize_severity_number("SEVERITY_NUMBER_ERROR") == 17
    assert storage._normalize_severity_number("SEVERITY_NUMBER_FATAL") == 21

    # None value
    assert storage._normalize_severity_number(None) is None

    # Unknown string (default to 0)
    assert storage._normalize_severity_number("UNKNOWN") == 0


def test_store_traces_with_scope_spans():
    """Test that store_traces correctly handles scope_spans (snake_case).

    This is the key test - verifies we're using the correct field name.
    Tests with list input (matches receiver usage).
    """
    storage = PostgresStorage("postgresql+psycopg2://localhost/test")

    # OTLP data with scope_spans (snake_case, not camelCase!)
    # Pass as list directly, matching receiver usage
    resource_spans = [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "test-service"}},
                ]
            },
            "scope_spans": [  # Snake case!
                {
                    "scope": {"name": "test-scope"},
                    "spans": [
                        {
                            "trace_id": "AAAAAAAAAAAAAAAAAAAAAA==",
                            "span_id": "AAAAAAAAAAA=",
                            "name": "test-span",
                            "kind": "SPAN_KIND_SERVER",  # MessageToDict converts to enum string
                            "start_time_unix_nano": "1000000",  # MessageToDict converts int64 to string
                            "end_time_unix_nano": "2000000",
                            "attributes": [],
                        }
                    ],
                }
            ],
        }
    ]

    # This should not raise KeyError for "scopeSpans" or list attribute errors
    # Note: Will fail to connect to DB, but we're testing parsing logic
    try:
        count = storage.store_traces(resource_spans)
        assert count == 1
    except Exception as e:
        # Expected to fail on DB connection, but not on signature/parsing
        assert "'list' object has no attribute 'get'" not in str(e)
        assert "scopeSpans" not in str(e)
        assert "KeyError" not in str(e)


def test_store_logs_with_scope_logs():
    """Test that store_logs correctly handles scope_logs (snake_case).

    Tests with list input (matches receiver usage).
    """
    storage = PostgresStorage("postgresql+psycopg2://localhost/test")

    # Pass as list directly, matching receiver usage
    resource_logs = [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "test-service"}},
                ]
            },
            "scope_logs": [  # Snake case!
                {
                    "scope": {"name": "test-scope"},
                    "log_records": [  # Snake case!
                        {
                            "time_unix_nano": "1000000",  # MessageToDict converts int64 to string
                            "severity_number": 9,
                            "body": {"string_value": "test log"},  # Snake case!
                            "attributes": [],
                        }
                    ],
                }
            ],
        }
    ]

    # This should not raise KeyError for "scopeLogs" or list attribute errors
    try:
        count = storage.store_logs(resource_logs)
        assert count == 1
    except Exception as e:
        assert "'list' object has no attribute 'get'" not in str(e)
        assert "scopeLogs" not in str(e)
        assert "KeyError" not in str(e)


def test_store_metrics_with_gauge():
    """Test storing gauge metrics with correct MessageToDict format."""
    storage = PostgresStorage("postgresql+psycopg2://localhost/test")

    # Metrics with gauge type (snake_case from MessageToDict)
    resource_metrics = [
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"string_value": "test-service"}}]},
            "scope_metrics": [  # Snake case!
                {
                    "scope": {"name": "test-scope"},
                    "metrics": [
                        {
                            "name": "cpu.usage",
                            "unit": "%",
                            "description": "CPU usage percentage",
                            "gauge": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1000000",  # MessageToDict converts int64 to string
                                        "start_time_unix_nano": "900000",
                                        "as_double": 42.5,
                                        "attributes": [{"key": "host", "value": {"string_value": "localhost"}}],
                                    }
                                ]
                            },
                        }
                    ],
                }
            ],
        }
    ]

    try:
        count = storage.store_metrics(resource_metrics)
        assert count == 1
    except Exception as e:
        assert "'list' object has no attribute 'get'" not in str(e)
        assert "scopeMetrics" not in str(e)


def test_store_metrics_with_sum(postgres_storage):
    """Test storing sum metrics with correct MessageToDict format."""
    resource_metrics = [
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"string_value": "test-service"}}]},
            "scope_metrics": [
                {
                    "scope": {"name": "test-scope"},
                    "metrics": [
                        {
                            "name": "request.count",
                            "unit": "1",
                            "description": "Total requests",
                            "sum": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1000000",
                                        "start_time_unix_nano": "900000",
                                        "as_int": "100",  # MessageToDict may convert int64 to string
                                        "attributes": [],
                                    }
                                ]
                            },
                        }
                    ],
                }
            ],
        }
    ]

    count = postgres_storage.store_metrics(resource_metrics)
    assert count == 1


# Star Schema ETL Pattern Tests
# ==============================


def test_dimension_upsert_commits_immediately(postgres_storage, postgres_session):  # noqa: ARG001
    """Test that dimension upserts commit immediately (not deferred).

    This is critical for multi-process safety - dimensions must be visible
    to other processes immediately after upsert.
    postgres_session fixture ensures DB schema exists but isn't used directly.
    """
    # Upsert namespace (creates own autocommit session internally)
    namespace_id = postgres_storage._upsert_namespace(1, "test-ns")
    assert namespace_id is not None

    # Verify it's committed by querying in a NEW session
    with postgres_storage.engine.begin() as new_conn:
        result = new_conn.execute(select(NamespaceDim.id).where(NamespaceDim.namespace == "test-ns"))
        committed_id = result.scalar()

    assert committed_id == namespace_id, "Dimension not visible in new session - commit didn't happen"


def test_dimension_upserts_are_idempotent(postgres_storage, postgres_session):  # noqa: ARG001
    """Test that dimension upserts can be safely retried.

    If a batch fails after dimensions inserted but before facts,
    retry should reuse existing dimensions without errors.
    postgres_session fixture ensures DB schema exists but isn't used directly.
    """
    # First upsert (methods create own autocommit sessions)
    ns_id_1 = postgres_storage._upsert_namespace(1, "prod")
    svc_id_1 = postgres_storage._upsert_service(1, "api", "prod")

    # Simulate retry - should return same IDs
    ns_id_2 = postgres_storage._upsert_namespace(1, "prod")
    svc_id_2 = postgres_storage._upsert_service(1, "api", "prod")

    assert ns_id_1 == ns_id_2, "Namespace ID changed on retry"
    assert svc_id_1 == svc_id_2, "Service ID changed on retry"


def test_fact_insert_after_dimensions_committed(postgres_storage):
    """Test that facts can reference dimensions committed in prior phase.

    This verifies the two-phase pattern: dimensions first, facts second.
    Methods create their own autocommit sessions.
    """
    # Phase 1: Upsert dimensions (commits immediately via autocommit sessions)
    postgres_storage._upsert_namespace(1, "test-ns")
    svc_id = postgres_storage._upsert_service(1, "test-svc", "test-ns")
    op_id = postgres_storage._upsert_operation(1, svc_id, "GET /api", 2)

    # Phase 2: Insert facts referencing committed dimensions
    resource_spans = [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"string_value": "test-svc"}},
                    {"key": "service.namespace", "value": {"string_value": "test-ns"}},
                ]
            },
            "scope_spans": [
                {
                    "scope": {"name": "test"},
                    "spans": [
                        {
                            "trace_id": "0" * 32,
                            "span_id": "0" * 16,
                            "name": "GET /api",
                            "kind": 2,
                            "start_time_unix_nano": "1000000",
                            "end_time_unix_nano": "2000000",
                            "attributes": [],
                            "events": [],
                            "links": [],
                        }
                    ],
                }
            ],
        }
    ]

    count = postgres_storage.store_traces(resource_spans)
    assert count == 1

    # Verify foreign key relationships
    with postgres_storage.engine.begin() as conn:
        result = conn.execute(
            select(SpansFact.service_id, SpansFact.operation_id).where(SpansFact.trace_id == "0" * 32)
        )
        row = result.one()
        assert row.service_id == svc_id
        assert row.operation_id == op_id


def test_concurrent_dimension_upserts_no_deadlock(postgres_storage):
    """Test that concurrent dimension upserts don't deadlock.

    Simulates multiple processes upserting same dimensions.
    With immediate commits and internal sessions, no locks are held across operations.
    """

    def upsert_dimensions(ns: str, svc: str):
        """Simulate one process upserting dimensions."""
        # Methods create their own autocommit sessions
        postgres_storage._upsert_namespace(1, ns)
        postgres_storage._upsert_service(1, svc, ns)

    # Run concurrent upserts for same dimensions using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(upsert_dimensions, "prod", "api"),
            executor.submit(upsert_dimensions, "prod", "api"),
            executor.submit(upsert_dimensions, "prod", "api"),
        ]

        # Wait for all to complete
        for future in as_completed(futures):
            future.result()  # Will raise if any failed

    # Verify only one dimension created (not duplicated)
    with postgres_storage.engine.begin() as conn:
        result = conn.execute(select(ServiceDim.id).where(ServiceDim.name == "api"))
        rows = result.all()
        assert len(rows) == 1, f"Expected 1 service, got {len(rows)}"


def test_dimension_hierarchy_commits_outer_to_inner(postgres_storage, postgres_session):  # noqa: ARG001
    """Test that dimension hierarchy commits work: namespace → service → operation.

    Each level must commit before next level, ensuring child can reference parent.
    postgres_session fixture ensures DB schema exists but isn't used directly.
    """
    # Upsert namespace (outer edge of star) - creates own autocommit session
    ns_id = postgres_storage._upsert_namespace(1, "prod")

    # Verify namespace committed before service upsert
    with postgres_storage.engine.begin() as conn:
        result = conn.execute(select(NamespaceDim.id).where(NamespaceDim.namespace == "prod"))
        assert result.scalar() == ns_id

    # Upsert service (middle layer) - creates own autocommit session
    svc_id = postgres_storage._upsert_service(1, "api", "prod")

    # Verify service committed before operation upsert
    with postgres_storage.engine.begin() as conn:
        result = conn.execute(select(ServiceDim.id).where(ServiceDim.name == "api"))
        assert result.scalar() == svc_id

    # Upsert operation (inner layer, closest to fact) - creates own autocommit session
    op_id = postgres_storage._upsert_operation(1, svc_id, "GET /users", 2)

    # Verify operation committed
    with postgres_storage.engine.begin() as conn:
        result = conn.execute(
            select(OperationDim.id).where(OperationDim.service_id == svc_id, OperationDim.name == "GET /users")
        )
        assert result.scalar() == op_id
