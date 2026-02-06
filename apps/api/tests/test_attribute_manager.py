"""
Unit tests for AttributeManager.

Tests key caching, attribute type extraction, promotion routing,
drop filtering, and database interactions (mocked).
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.otlp_schema import AttributeKey
from app.storage.attribute_manager import AttributeManager


@pytest.fixture
def mock_engine():
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
def attribute_manager(mock_engine, mock_config):
    """Create AttributeManager with mocked engine and config."""
    return AttributeManager(mock_engine, mock_config)


def test_key_cache_hit(attribute_manager):
    """Test key ID retrieval from cache."""
    # Pre-populate cache
    attribute_manager._key_cache["service.name"] = 123

    key_id = attribute_manager.get_or_create_key_id("service.name")

    assert key_id == 123
    # Should not query database
    attribute_manager.session.exec.assert_not_called()


def test_key_cache_miss_existing_key(attribute_manager, mock_session):
    """Test key ID retrieval from database (cache miss, key exists)."""
    # Mock database response
    mock_key = AttributeKey(key_id=456, key="http.status_code")
    mock_result = MagicMock()
    mock_result.first.return_value = mock_key
    mock_session.exec.return_value = mock_result

    key_id = attribute_manager.get_or_create_key_id("http.status_code")

    assert key_id == 456
    # Should be cached now
    assert attribute_manager._key_cache["http.status_code"] == 456
    mock_session.exec.assert_called_once()


def test_key_creation_new_key(attribute_manager, mock_session):
    """Test creating new attribute key."""
    # First query returns None (key doesn't exist)
    # Upsert happens (no return value needed from exec for upsert)
    # Second query returns the new key
    mock_key = AttributeKey(key_id=789, key="custom.attribute")
    mock_result_none = MagicMock()
    mock_result_none.first.return_value = None
    mock_result_with_key = MagicMock()
    mock_result_with_key.first.return_value = mock_key

    # First call: initial query (None), second call: upsert statement, third call: query again
    mock_session.exec.side_effect = [
        mock_result_none,  # Initial query
        MagicMock(),  # Upsert statement execution (no return needed)
        mock_result_with_key,  # Final query
    ]

    key_id = attribute_manager.get_or_create_key_id("custom.attribute")

    assert key_id == 789
    # Should be cached
    assert attribute_manager._key_cache["custom.attribute"] == 789
    # Should have called exec 3 times (initial query, upsert, final query)
    assert mock_session.exec.call_count == 3
    mock_session.commit.assert_called_once()


def test_extract_string_value(attribute_manager):
    """Test extracting string value from OTLP AnyValue."""
    any_value = {"stringValue": "example"}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "string"
    assert value == "example"


def test_extract_int_value_from_int(attribute_manager):
    """Test extracting int value from integer."""
    any_value = {"intValue": 42}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "int"
    assert value == 42


def test_extract_int_value_from_string(attribute_manager):
    """Test extracting int value from string (OTLP compatibility)."""
    any_value = {"intValue": "123"}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "int"
    assert value == 123


def test_extract_double_value(attribute_manager):
    """Test extracting double value from OTLP AnyValue."""
    any_value = {"doubleValue": 3.14}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "double"
    assert value == 3.14


def test_extract_bool_value(attribute_manager):
    """Test extracting bool value from OTLP AnyValue."""
    any_value = {"boolValue": True}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "bool"
    assert value is True


def test_extract_bytes_value(attribute_manager):
    """Test extracting bytes value from OTLP AnyValue."""
    any_value = {"bytesValue": "YmFzZTY0ZGF0YQ=="}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "bytes"
    assert value == "YmFzZTY0ZGF0YQ=="


def test_extract_array_value_as_other(attribute_manager):
    """Test extracting array value (stored as other/JSONB)."""
    any_value = {"arrayValue": {"values": [{"stringValue": "a"}, {"intValue": 1}]}}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "other"
    assert value == any_value


def test_extract_kvlist_value_as_other(attribute_manager):
    """Test extracting kvlist value (stored as other/JSONB)."""
    any_value = {"kvlistValue": {"values": [{"key": "nested", "value": {"stringValue": "x"}}]}}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type == "other"
    assert value == any_value


def test_extract_unknown_value_returns_none(attribute_manager):
    """Test handling unknown AnyValue structure."""
    any_value = {"unknownField": "value"}
    value_type, value = attribute_manager._extract_type_and_value(any_value)

    assert value_type is None
    assert value is None


def test_store_attributes_dropped(attribute_manager, mock_config):
    """Test that dropped attributes are not stored."""
    mock_config.should_drop.side_effect = lambda k: k == "password"

    attributes = {
        "password": {"stringValue": "secret"},
        "username": {"stringValue": "alice"},
    }

    promoted, other = attribute_manager.store_attributes(
        signal="logs", entity_id=1, attributes=attributes, table_classes={}
    )

    # Password should be dropped
    assert "password" not in promoted
    assert "password" not in other
    # Username should be in other (not promoted by mock config)
    assert "username" in other


def test_store_attributes_promoted(attribute_manager, mock_config, mock_session):
    """Test storing promoted attributes to typed tables."""
    # Setup: service.name is promoted as string
    mock_config.is_promoted.side_effect = lambda _signal, key, vtype: key == "service.name" and vtype == "string"

    # Mock key ID lookup
    attribute_manager._key_cache = {"service.name": 100}

    # Mock table classes
    mock_string_table = MagicMock()
    table_classes = {"string": mock_string_table}

    attributes = {"service.name": {"stringValue": "my-service"}}

    promoted, other = attribute_manager.store_attributes(
        signal="logs", entity_id=1, attributes=attributes, table_classes=table_classes
    )

    # Should be promoted
    assert "service.name" in promoted
    assert promoted["service.name"] == "my-service"
    assert "service.name" not in other

    # Should add to session
    mock_session.add.assert_called_once()


def test_store_attributes_not_promoted_goes_to_other(attribute_manager, mock_config, mock_session):
    """Test that non-promoted attributes go to other_attrs."""
    # No attributes are promoted
    mock_config.is_promoted.return_value = False

    attributes = {"custom.attr": {"stringValue": "value"}}

    promoted, other = attribute_manager.store_attributes(
        signal="logs", entity_id=1, attributes=attributes, table_classes={}
    )

    # Should be in other (JSONB)
    assert "custom.attr" in other
    assert other["custom.attr"] == "value"
    assert "custom.attr" not in promoted

    # Should not add to typed table
    mock_session.add.assert_not_called()


def test_store_attributes_multiple_types(attribute_manager, mock_config, mock_session):
    """Test storing attributes of multiple types."""

    # Promote string and int types
    def is_promoted_side_effect(_signal, key, vtype):
        return (key == "http.method" and vtype == "string") or (key == "http.status_code" and vtype == "int")

    mock_config.is_promoted.side_effect = is_promoted_side_effect

    # Mock key IDs
    attribute_manager._key_cache = {"http.method": 101, "http.status_code": 102}

    # Mock table classes
    mock_string_table = MagicMock()
    mock_int_table = MagicMock()
    table_classes = {"string": mock_string_table, "int": mock_int_table}

    attributes = {
        "http.method": {"stringValue": "GET"},
        "http.status_code": {"intValue": 200},
    }

    promoted, other = attribute_manager.store_attributes(
        signal="logs", entity_id=1, attributes=attributes, table_classes=table_classes
    )

    # Both should be promoted
    assert "http.method" in promoted
    assert "http.status_code" in promoted
    assert len(other) == 0

    # Should add both to session
    assert mock_session.add.call_count == 2


@pytest.mark.skip(reason="get_attributes requires real SQLModel classes, not MagicMock (SQLAlchemy constraint)")
def test_get_attributes_empty(attribute_manager, mock_session):
    """Test retrieving attributes when none exist."""
    # Mock empty results
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.exec.return_value = mock_result

    attributes = attribute_manager.get_attributes(entity_id=1, signal="logs", table_classes={"string": MagicMock()})

    assert attributes == {}


@pytest.mark.skip(reason="get_attributes requires real SQLModel classes, not MagicMock (SQLAlchemy constraint)")
def test_get_attributes_with_promoted(attribute_manager, mock_session):
    """Test retrieving promoted attributes from typed tables."""
    # Mock attribute key
    mock_key = MagicMock()
    mock_key.key = "service.name"

    # Mock table record
    mock_record = MagicMock()
    mock_record.value = "my-service"

    # Mock query result
    mock_result = MagicMock()
    mock_result.all.return_value = [(mock_record, mock_key)]
    mock_session.exec.return_value = mock_result

    mock_table = MagicMock()
    mock_table.key_id = "key_id"  # For join condition
    table_classes = {"string": mock_table}

    attributes = attribute_manager.get_attributes(entity_id=1, signal="logs", table_classes=table_classes)

    assert "service.name" in attributes
    assert attributes["service.name"] == "my-service"


def test_clear_cache(attribute_manager):
    """Test clearing key cache."""
    attribute_manager._key_cache = {"key1": 1, "key2": 2}
    assert attribute_manager.get_cache_size() == 2

    attribute_manager.clear_cache()

    assert attribute_manager.get_cache_size() == 0
    assert len(attribute_manager._key_cache) == 0


def test_get_cache_size(attribute_manager):
    """Test getting cache size."""
    assert attribute_manager.get_cache_size() == 0

    attribute_manager._key_cache = {"key1": 1, "key2": 2, "key3": 3}

    assert attribute_manager.get_cache_size() == 3
