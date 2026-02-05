"""
Unit tests for LogsStorage.

Tests OTLP log record ingestion, resource/scope handling,
attribute promotion integration, and basic querying.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.storage.logs_storage import LogsStorage


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.commit = MagicMock()
    session.exec = MagicMock()
    return session


@pytest.fixture
def logs_storage(mock_session):
    """Create LogsStorage with mocked dependencies."""
    with (
        patch("app.storage.logs_storage.ResourceManager") as mock_rm,
        patch("app.storage.logs_storage.AttributeManager") as mock_am,
    ):
        storage = LogsStorage(mock_session)
        storage.resource_manager = mock_rm.return_value
        storage.attribute_manager = mock_am.return_value
        return storage


def test_flatten_otlp_attributes_string(logs_storage):
    """Test flattening OTLP string attributes."""
    otlp_attrs = [
        {"key": "service.name", "value": {"stringValue": "my-service"}},
        {"key": "environment", "value": {"stringValue": "production"}},
    ]

    flattened = logs_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened == {"service.name": "my-service", "environment": "production"}


def test_flatten_otlp_attributes_int(logs_storage):
    """Test flattening OTLP int attributes."""
    otlp_attrs = [
        {"key": "status_code", "value": {"intValue": 200}},
        {"key": "retry_count", "value": {"intValue": "3"}},  # String int
    ]

    flattened = logs_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened == {"status_code": 200, "retry_count": 3}


def test_flatten_otlp_attributes_mixed_types(logs_storage):
    """Test flattening OTLP attributes of various types."""
    otlp_attrs = [
        {"key": "str_attr", "value": {"stringValue": "value"}},
        {"key": "int_attr", "value": {"intValue": 42}},
        {"key": "double_attr", "value": {"doubleValue": 3.14}},
        {"key": "bool_attr", "value": {"boolValue": True}},
        {"key": "bytes_attr", "value": {"bytesValue": "YmFzZTY0"}},
    ]

    flattened = logs_storage._flatten_otlp_attributes(otlp_attrs)

    assert flattened["str_attr"] == "value"
    assert flattened["int_attr"] == 42
    assert flattened["double_attr"] == 3.14
    assert flattened["bool_attr"] is True
    assert flattened["bytes_attr"] == "YmFzZTY0"


def test_flatten_otlp_attributes_complex(logs_storage):
    """Test flattening OTLP complex attributes."""
    otlp_attrs = [
        {
            "key": "complex",
            "value": {"kvlistValue": {"values": [{"key": "nested", "value": {}}]}},
        }
    ]

    flattened = logs_storage._flatten_otlp_attributes(otlp_attrs)

    assert "complex" in flattened
    assert isinstance(flattened["complex"], dict)


def test_store_logs_single_record(logs_storage, mock_session):
    """Test storing a single log record."""
    # Mock resource manager
    logs_storage.resource_manager.get_or_create_resource.return_value = (1, True, "hash1")
    logs_storage.resource_manager.get_or_create_scope.return_value = (2, True, "hash2")

    # Mock attribute manager
    logs_storage.attribute_manager.store_attributes.return_value = (
        {"log.level": "INFO"},
        {"custom.attr": "value"},
    )

    # Mock flush to set log_id
    def set_log_id(log_fact):
        log_fact.log_id = 123

    mock_session.flush.side_effect = set_log_id

    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test-service"}}]},
                "scopeLogs": [
                    {
                        "scope": {"name": "test.logger", "version": "1.0.0"},
                        "logRecords": [
                            {
                                "timeUnixNano": "1700000000000000000",
                                "observedTimeUnixNano": "1700000000000000001",
                                "severityNumber": 9,
                                "severityText": "INFO",
                                "body": {"stringValue": "Test log message"},
                                "attributes": [{"key": "log.level", "value": {"stringValue": "INFO"}}],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    stats = logs_storage.store_logs(otlp_logs)

    assert stats["logs_stored"] == 1
    assert stats["resources_created"] == 1
    assert stats["scopes_created"] == 1
    assert stats["attributes_promoted"] == 1
    assert stats["attributes_other"] == 1
    mock_session.commit.assert_called_once()


def test_store_logs_multiple_records(logs_storage, mock_session):
    """Test storing multiple log records."""
    logs_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash1")
    logs_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash2")
    logs_storage.attribute_manager.store_attributes.return_value = ({}, {})

    # Mock flush
    mock_session.flush.side_effect = lambda x: setattr(x, "log_id", 123)

    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {"attributes": []},
                "scopeLogs": [
                    {
                        "scope": {"name": "logger", "version": "1.0"},
                        "logRecords": [
                            {
                                "timeUnixNano": "1700000000000000000",
                                "severityNumber": 9,
                                "body": {"stringValue": "Log 1"},
                            },
                            {
                                "timeUnixNano": "1700000000000000001",
                                "severityNumber": 13,
                                "body": {"stringValue": "Log 2"},
                            },
                            {
                                "timeUnixNano": "1700000000000000002",
                                "severityNumber": 17,
                                "body": {"stringValue": "Log 3"},
                            },
                        ],
                    }
                ],
            }
        ]
    }

    stats = logs_storage.store_logs(otlp_logs)

    assert stats["logs_stored"] == 3
    # Resource/scope reused (not created again)
    assert stats["resources_created"] == 0
    assert stats["scopes_created"] == 0


def test_store_logs_with_trace_correlation(logs_storage, mock_session):
    """Test storing logs with trace/span correlation."""
    logs_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    logs_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    logs_storage.attribute_manager.store_attributes.return_value = ({}, {})

    mock_session.flush.side_effect = lambda x: setattr(x, "log_id", 456)

    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {"attributes": []},
                "scopeLogs": [
                    {
                        "scope": {"name": "logger", "version": "1.0"},
                        "logRecords": [
                            {
                                "timeUnixNano": "1700000000000000000",
                                "severityNumber": 9,
                                "body": {"stringValue": "Correlated log"},
                                "traceId": "ABC1234567890DEF",
                                "spanId": "123456789ABCDEF0",
                                "attributes": [],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    logs_storage.store_logs(otlp_logs)

    # Verify log fact was created with trace correlation
    calls = list(mock_session.add.call_args_list)
    log_fact_call = [c for c in calls if hasattr(c[0][0], "trace_id")]
    assert len(log_fact_call) > 0
    log_fact = log_fact_call[0][0][0]
    assert log_fact.trace_id == "abc1234567890def"  # Lowercase
    assert log_fact.span_id == "123456789abcdef0"  # Lowercase


def test_store_logs_with_bytes_trace_id(logs_storage, mock_session):
    """Test storing logs with bytes trace_id (some SDKs send bytes)."""
    logs_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    logs_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")
    logs_storage.attribute_manager.store_attributes.return_value = ({}, {})

    mock_session.flush.side_effect = lambda x: setattr(x, "log_id", 789)

    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {"attributes": []},
                "scopeLogs": [
                    {
                        "scope": {"name": "logger", "version": "1.0"},
                        "logRecords": [
                            {
                                "timeUnixNano": "1700000000000000000",
                                "severityNumber": 9,
                                "body": {"stringValue": "Log with bytes IDs"},
                                "traceId": b"\xab\xcd\xef\x01\x23\x45\x67\x89\xab\xcd\xef\x01\x23\x45\x67\x89",
                                "spanId": b"\x12\x34\x56\x78\x9a\xbc\xde\xf0",
                                "attributes": [],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    logs_storage.store_logs(otlp_logs)

    # Verify hex conversion
    log_fact_call = [c for c in mock_session.add.call_args_list if hasattr(c[0][0], "trace_id") and c[0][0].trace_id]
    assert len(log_fact_call) > 0
    log_fact = log_fact_call[0][0][0]
    assert log_fact.trace_id == "abcdef0123456789abcdef0123456789"
    assert log_fact.span_id == "123456789abcdef0"


def test_store_logs_with_attributes_other(logs_storage, mock_session):
    """Test storing logs with other (non-promoted) attributes."""
    logs_storage.resource_manager.get_or_create_resource.return_value = (1, False, "hash")
    logs_storage.resource_manager.get_or_create_scope.return_value = (2, False, "hash")

    # Simulate some attributes going to "other"
    logs_storage.attribute_manager.store_attributes.return_value = (
        {"log.level": "ERROR"},
        {"custom.field": "custom-value", "request.id": "req-123"},
    )

    mock_session.flush.side_effect = lambda x: setattr(x, "log_id", 999)

    otlp_logs = {
        "resourceLogs": [
            {
                "resource": {"attributes": []},
                "scopeLogs": [
                    {
                        "scope": {"name": "logger", "version": "1.0"},
                        "logRecords": [
                            {
                                "timeUnixNano": "1700000000000000000",
                                "severityNumber": 17,
                                "body": {"stringValue": "Error log"},
                                "attributes": [
                                    {"key": "log.level", "value": {"stringValue": "ERROR"}},
                                    {
                                        "key": "custom.field",
                                        "value": {"stringValue": "custom-value"},
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    stats = logs_storage.store_logs(otlp_logs)

    # Verify attributes_other was set on log fact
    other_calls = [
        c
        for c in mock_session.add.call_args_list
        if hasattr(c[0][0], "attributes_other") and c[0][0].attributes_other is not None
    ]
    assert len(other_calls) > 0
    assert stats["attributes_other"] == 2


def test_get_logs_basic_query(logs_storage, mock_session):
    """Test basic log querying."""
    # Mock query results
    mock_log = MagicMock()
    mock_log.log_id = 1
    mock_log.time_unix_nano = 1700000000000000000
    mock_log.severity_number = 9
    mock_log.severity_text = "INFO"
    mock_log.body = "Test log"
    mock_log.trace_id = None
    mock_log.span_id = None
    mock_log.resource_id = 1
    mock_log.scope_id = 2

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_log]
    mock_session.exec.return_value = mock_result

    logs = logs_storage.get_logs(start_time=1700000000000000000, end_time=1700000001000000000, limit=10)

    assert len(logs) == 1
    assert logs[0]["log_id"] == 1
    assert logs[0]["body"] == "Test log"
    assert logs[0]["severity_number"] == 9


def test_get_logs_with_severity_filter(logs_storage, mock_session):
    """Test log querying with severity filter."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    logs_storage.get_logs(
        start_time=1700000000000000000,
        end_time=1700000001000000000,
        severity_min=13,  # WARN or higher
        limit=10,
    )

    # Verify session.exec was called (query executed)
    assert mock_session.exec.called


def test_get_logs_with_trace_id_filter(logs_storage, mock_session):
    """Test log querying with trace ID filter."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    logs_storage.get_logs(
        start_time=1700000000000000000,
        end_time=1700000001000000000,
        trace_id="ABC123",
        limit=10,
    )

    # Verify query executed
    assert mock_session.exec.called
