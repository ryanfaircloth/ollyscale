"""
Unit tests for TracesStorage.

Tests OTLP span record ingestion, resource/scope handling,
attribute promotion integration, parent-child relationships, and basic querying.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.storage.traces_storage import TracesStorage


@pytest.fixture
def mock_engine():
    """Create mock database engine (transactional)."""
    engine = MagicMock()
    return engine


@pytest.fixture
def mock_autocommit_engine():
    """Create mock database engine (autocommit)."""
    engine = MagicMock()
    return engine


@pytest.fixture
def mock_config():
    """Create mock AttributePromotionConfig."""
    config = MagicMock()
    config.is_promoted = MagicMock(return_value=False)
    return config


@pytest.fixture
def traces_storage(mock_engine, mock_autocommit_engine, mock_config):
    """Create TracesStorage with mocked dependencies."""
    with (
        patch("app.storage.traces_storage.ResourceManager") as mock_rm,
        patch("app.storage.traces_storage.AttributeManager") as mock_am,
    ):
        storage = TracesStorage(mock_engine, mock_autocommit_engine, mock_config)
        storage.resource_mgr = mock_rm.return_value
        storage.attr_mgr = mock_am.return_value
        return storage


def test_flatten_otlp_attributes_string(traces_storage):
    """Test flattening OTLP string attributes."""
    otlp_attrs = [
        {"key": "http.method", "value": {"stringValue": "GET"}},
        {"key": "http.route", "value": {"stringValue": "/api/users"}},
    ]

    flattened = traces_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened == {"http.method": "GET", "http.route": "/api/users"}


def test_flatten_otlp_attributes_int(traces_storage):
    """Test flattening OTLP int attributes."""
    otlp_attrs = [
        {"key": "http.status_code", "value": {"intValue": 200}},
        {"key": "http.response.body.size", "value": {"intValue": "1024"}},  # String int
    ]

    flattened = traces_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened == {"http.status_code": 200, "http.response.body.size": 1024}


def test_flatten_otlp_attributes_mixed_types(traces_storage):
    """Test flattening OTLP attributes of various types."""
    otlp_attrs = [
        {"key": "str_attr", "value": {"stringValue": "value"}},
        {"key": "int_attr", "value": {"intValue": 42}},
        {"key": "double_attr", "value": {"doubleValue": 3.14}},
        {"key": "bool_attr", "value": {"boolValue": True}},
        {"key": "bytes_attr", "value": {"bytesValue": "YmFzZTY0"}},
    ]

    flattened = traces_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened["str_attr"] == "value"
    assert flattened["int_attr"] == 42
    assert flattened["double_attr"] == 3.14
    assert flattened["bool_attr"] is True
    assert flattened["bytes_attr"] == "YmFzZTY0"


def test_store_traces_single_span(traces_storage, mock_session):
    """Test storing a single span."""
    # Mock resource manager
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, True, "hash1")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, True, "hash2")

    # Mock attribute manager
    traces_storage.attribute_manager.store_attributes.return_value = (
        {"http.method": "GET"},
        {"custom.attr": "value"},
    )

    # Track objects added to session and set IDs on flush
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = 123
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    resource_spans = {
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test-service"}}]},
        "scopeSpans": [
            {
                "scope": {"name": "test.tracer", "version": "1.0.0"},
                "spans": [
                    {
                        "traceId": "ABC1234567890DEF",
                        "spanId": "123456789ABCDEF0",
                        "name": "GET /api/users",
                        "kind": 2,  # SPAN_KIND_CLIENT
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000123456789",
                        "status": {"code": 0},  # STATUS_CODE_OK
                        "attributes": [{"key": "http.method", "value": {"stringValue": "GET"}}],
                    }
                ],
            }
        ],
    }

    stats = traces_storage.store_traces(resource_spans)

    assert stats["spans_stored"] == 1
    assert stats["resources_created"] == 1
    assert stats["scopes_created"] == 1
    assert stats["attributes_promoted"] == 1
    assert stats["attributes_other"] == 1


def test_store_traces_multiple_spans(traces_storage, mock_session):
    """Test storing multiple spans in a trace."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash1")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash2")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    span_id_counter = [100]
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = span_id_counter[0]
                span_id_counter[0] += 1
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": "ABC123",
                        "spanId": "SPAN001",
                        "name": "Span 1",
                        "kind": 1,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000100000000",
                        "status": {"code": 0},
                    },
                    {
                        "traceId": "ABC123",
                        "spanId": "SPAN002",
                        "name": "Span 2",
                        "kind": 2,
                        "startTimeUnixNano": "1700000000200000000",
                        "endTimeUnixNano": "1700000000300000000",
                        "status": {"code": 0},
                    },
                ],
            }
        ],
    }

    stats = traces_storage.store_traces(resource_spans)

    assert stats["spans_stored"] == 2
    # Resource/scope reused (not created again)
    assert stats["resources_created"] == 0
    assert stats["scopes_created"] == 0


def test_store_traces_with_parent_child(traces_storage, mock_session):
    """Test storing spans with parent-child relationships."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    span_id_counter = [200]
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = span_id_counter[0]
                span_id_counter[0] += 1
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": "TRACE123",
                        "spanId": "PARENTSPAN1",
                        "name": "Parent Span",
                        "kind": 1,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000500000000",
                        "status": {"code": 0},
                    },
                    {
                        "traceId": "TRACE123",
                        "spanId": "CHILDSPAN1",
                        "parentSpanId": "PARENTSPAN1",
                        "name": "Child Span",
                        "kind": 2,
                        "startTimeUnixNano": "1700000000100000000",
                        "endTimeUnixNano": "1700000000200000000",
                        "status": {"code": 0},
                    },
                ],
            }
        ],
    }

    traces_storage.store_traces(resource_spans)

    # Verify both spans were created
    calls = list(mock_session.add.call_args_list)
    span_fact_calls = [c for c in calls if hasattr(c[0][0], "trace_id")]
    assert len(span_fact_calls) == 2

    # Verify child span has parent_span_id_hex
    child_span = span_fact_calls[1][0][0]
    assert child_span.parent_span_id_hex == "parentspan1"  # Lowercase


def test_store_traces_with_bytes_ids(traces_storage, mock_session):
    """Test storing spans with bytes IDs (some SDKs send bytes)."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = 300
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    # Simulate bytes IDs (hex-encoded in test)
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": b"ABC123".hex(),
                        "spanId": b"SPAN01".hex(),
                        "name": "Bytes ID Span",
                        "kind": 1,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000100000000",
                        "status": {"code": 0},
                    }
                ],
            }
        ],
    }

    traces_storage.store_traces(resource_spans)

    # Verify span fact was created with converted IDs
    calls = list(mock_session.add.call_args_list)
    span_fact_call = [c for c in calls if hasattr(c[0][0], "trace_id")]
    assert len(span_fact_call) > 0


def test_store_traces_with_status_error(traces_storage, mock_session):
    """Test storing spans with error status."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = 400
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": "ERROR_TRACE",
                        "spanId": "ERROR_SPAN",
                        "name": "Failed Operation",
                        "kind": 3,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000100000000",
                        "status": {"code": 2, "message": "Internal server error"},  # STATUS_CODE_ERROR
                    }
                ],
            }
        ],
    }

    traces_storage.store_traces(resource_spans)

    # Verify span fact was created with error status
    calls = list(mock_session.add.call_args_list)
    span_fact_call = [c for c in calls if hasattr(c[0][0], "status_code")]
    assert len(span_fact_call) > 0
    span_fact = span_fact_call[0][0][0]
    assert span_fact.status_code == 2
    assert span_fact.status_message == "Internal server error"


def test_store_traces_empty_resource_spans(traces_storage):
    """Test handling empty resourceSpans."""
    # Mock resource manager to handle empty attributes
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")

    # Single ResourceSpans entry with no spans
    resource_spans = {"resource": {"attributes": []}, "scopeSpans": []}

    stats = traces_storage.store_traces(resource_spans)

    assert stats["spans_stored"] == 0
    assert stats["resources_created"] == 0
    assert stats["scopes_created"] == 0


def test_store_traces_missing_status(traces_storage, mock_session):
    """Test storing spans without status field."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = 500
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": "TRACE_NO_STATUS",
                        "spanId": "SPAN_NO_STATUS",
                        "name": "No Status Span",
                        "kind": 1,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000100000000",
                        # No status field
                    }
                ],
            }
        ],
    }

    traces_storage.store_traces(resource_spans)

    # Verify span fact was created with default status
    calls = list(mock_session.add.call_args_list)
    span_fact_call = [c for c in calls if hasattr(c[0][0], "status_code")]
    assert len(span_fact_call) > 0
    span_fact = span_fact_call[0][0][0]
    assert span_fact.status_code == 0  # Default: STATUS_CODE_UNSET


def test_store_traces_span_kind_values(traces_storage, mock_session):
    """Test storing spans with different span kind values."""
    traces_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    traces_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    traces_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Track objects added to session and set IDs on flush
    span_id_counter = [600]
    added_objects = []
    mock_session.add.side_effect = lambda obj: added_objects.append(obj)

    def flush_side_effect():
        for obj in added_objects:
            if hasattr(obj, "span_id") and obj.span_id is None:
                obj.span_id = span_id_counter[0]
                span_id_counter[0] += 1
        added_objects.clear()

    mock_session.flush.side_effect = flush_side_effect

    # Single ResourceSpans entry (not wrapped in array)
    # Test all 5 SpanKind values
    resource_spans = {
        "resource": {"attributes": []},
        "scopeSpans": [
            {
                "scope": {"name": "tracer", "version": "1.0"},
                "spans": [
                    {
                        "traceId": "TRACE1",
                        "spanId": f"SPAN{kind}",
                        "name": f"Kind {kind}",
                        "kind": kind,
                        "startTimeUnixNano": "1700000000000000000",
                        "endTimeUnixNano": "1700000000100000000",
                        "status": {"code": 0},
                    }
                    for kind in [0, 1, 2, 3, 4, 5]  # All SpanKind values
                ],
            }
        ],
    }

    stats = traces_storage.store_traces(resource_spans)

    assert stats["spans_stored"] == 6


def test_get_traces_query_execution(traces_storage, mock_session):
    """Test get_traces executes SQL query."""
    mock_result = MagicMock()
    # fetchall() returns list of tuples: (trace_id, trace_start, trace_end, duration, span_count, service_name)
    mock_result.fetchall.return_value = [
        ("abc123", 1700000000000000000, 1700000000500000000, 500000000, 5, "test-service")
    ]
    mock_session.exec.return_value = mock_result

    traces = traces_storage.get_traces(
        start_time=1700000000000000000, end_time=1700000001000000000, limit=100, offset=0
    )

    assert len(traces) == 1
    assert traces[0]["trace_id"] == "abc123"
    assert traces[0]["span_count"] == 5
    assert traces[0]["service_name"] == "test-service"
    mock_session.exec.assert_called_once()


def test_get_trace_spans_query_execution(traces_storage, mock_session):
    """Test get_trace_spans executes SQL query."""
    mock_result = MagicMock()
    # fetchall() returns list of tuples: (span_id, trace_id, span_id_hex, parent_span_id_hex,
    #   name, kind, start_time_unix_nano, end_time_unix_nano, status_code, status_message,
    #   resource_id, resource_attributes, scope_id, scope_name, scope_version, attributes, service_name, semantic_type)
    mock_result.fetchall.return_value = [
        (
            123,
            "abc123",
            "span001",
            None,
            "Root Span",
            1,
            1700000000000000000,
            1700000000100000000,
            0,
            None,
            1,
            {"service.name": "test"},
            2,
            "tracer",
            "1.0",
            {},
            "test",
            None,
        ),
        (
            124,
            "abc123",
            "span002",
            "span001",
            "Child Span",
            2,
            1700000000010000000,
            1700000000050000000,
            0,
            None,
            1,
            {"service.name": "test"},
            2,
            "tracer",
            "1.0",
            {},
            "test",
            None,
        ),
    ]
    mock_session.exec.return_value = mock_result

    spans = traces_storage.get_trace_spans(trace_id="abc123")

    assert len(spans) == 2
    assert spans[0]["name"] == "Root Span"
    assert spans[0]["parent_span_id_hex"] is None
    assert spans[1]["name"] == "Child Span"
    assert spans[1]["parent_span_id_hex"] == "span001"
    mock_session.exec.assert_called_once()
