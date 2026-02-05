"""
Unit tests for ResourceManager.

Tests hash calculation, deduplication, service.name/namespace extraction,
last_seen updates, and caching behavior.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.models.otlp_schema import OtelResourcesDim, OtelScopesDim
from app.storage.resource_manager import ResourceManager


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = MagicMock()
    session.exec = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    return session


@pytest.fixture
def resource_manager(mock_session):
    """Create ResourceManager with mocked session."""
    return ResourceManager(mock_session)


def test_calculate_resource_hash_consistency(resource_manager):
    """Test that same attributes produce same hash."""
    attrs1 = {"service.name": "api", "cloud.provider": "aws"}
    attrs2 = {"service.name": "api", "cloud.provider": "aws"}

    hash1 = resource_manager.calculate_resource_hash(attrs1)
    hash2 = resource_manager.calculate_resource_hash(attrs2)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest


def test_calculate_resource_hash_key_order_independence(resource_manager):
    """Test that attribute order doesn't affect hash."""
    attrs1 = {"service.name": "api", "cloud.provider": "aws"}
    attrs2 = {"cloud.provider": "aws", "service.name": "api"}  # Different order

    hash1 = resource_manager.calculate_resource_hash(attrs1)
    hash2 = resource_manager.calculate_resource_hash(attrs2)

    assert hash1 == hash2


def test_calculate_resource_hash_different_values(resource_manager):
    """Test that different attributes produce different hashes."""
    attrs1 = {"service.name": "api"}
    attrs2 = {"service.name": "web"}

    hash1 = resource_manager.calculate_resource_hash(attrs1)
    hash2 = resource_manager.calculate_resource_hash(attrs2)

    assert hash1 != hash2


def test_extract_service_name(resource_manager):
    """Test service.name extraction."""
    attrs = {"service.name": "my-service", "other.attr": "value"}

    service_name = resource_manager._extract_service_name(attrs)

    assert service_name == "my-service"


def test_extract_service_name_missing(resource_manager):
    """Test service.name extraction when not present."""
    attrs = {"other.attr": "value"}

    service_name = resource_manager._extract_service_name(attrs)

    assert service_name is None


def test_extract_service_namespace(resource_manager):
    """Test service.namespace extraction."""
    attrs = {"service.namespace": "production", "service.name": "api"}

    service_namespace = resource_manager._extract_service_namespace(attrs)

    assert service_namespace == "production"


def test_extract_service_namespace_missing(resource_manager):
    """Test service.namespace extraction when not present."""
    attrs = {"service.name": "api"}

    service_namespace = resource_manager._extract_service_namespace(attrs)

    assert service_namespace is None


def test_get_or_create_resource_cache_hit(resource_manager):
    """Test resource lookup from cache."""
    attrs = {"service.name": "api"}
    resource_hash = resource_manager.calculate_resource_hash(attrs)

    # Pre-populate cache
    resource_manager._resource_cache[resource_hash] = 123

    # Mock last_seen update
    mock_resource = MagicMock()
    mock_session = resource_manager.session
    mock_result = MagicMock()
    mock_result.first.return_value = mock_resource
    mock_session.exec.return_value = mock_result

    resource_id, created, returned_hash = resource_manager.get_or_create_resource(attrs)

    assert resource_id == 123
    assert created is False
    assert returned_hash == resource_hash
    # Should not insert (cache hit)


def test_get_or_create_resource_db_hit(resource_manager, mock_session):
    """Test resource lookup from database (cache miss)."""
    attrs = {"service.name": "api"}
    resource_hash = resource_manager.calculate_resource_hash(attrs)

    # Mock database response
    mock_resource = OtelResourcesDim(
        resource_id=456,
        resource_hash=resource_hash,
        service_name="api",
        service_namespace=None,
        attributes=attrs,
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )

    # First query: find existing, second query: last_seen update lookup
    mock_result1 = MagicMock()
    mock_result1.first.return_value = mock_resource
    mock_result2 = MagicMock()
    mock_result2.first.return_value = mock_resource
    mock_session.exec.side_effect = [mock_result1, mock_result2]

    resource_id, created, returned_hash = resource_manager.get_or_create_resource(attrs)

    assert resource_id == 456
    assert created is False
    assert returned_hash == resource_hash
    # Should be cached now
    assert resource_manager._resource_cache[resource_hash] == 456


def test_get_or_create_resource_create_new(resource_manager, mock_session):
    """Test creating new resource record."""
    attrs = {"service.name": "new-service", "service.namespace": "dev"}
    resource_hash = resource_manager.calculate_resource_hash(attrs)

    # Mock: first query returns None, second query returns new resource
    mock_resource = OtelResourcesDim(
        resource_id=789,
        resource_hash=resource_hash,
        service_name="new-service",
        service_namespace="dev",
        attributes=attrs,
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )

    mock_result_none = MagicMock()
    mock_result_none.first.return_value = None
    mock_result_with_resource = MagicMock()
    mock_result_with_resource.first.return_value = mock_resource

    mock_session.exec.side_effect = [
        mock_result_none,  # Initial query
        MagicMock(),  # Upsert execution
        mock_result_with_resource,  # Final query
    ]

    resource_id, created, returned_hash = resource_manager.get_or_create_resource(attrs)

    assert resource_id == 789
    assert created is True
    assert returned_hash == resource_hash
    # Should be cached
    assert resource_manager._resource_cache[resource_hash] == 789
    mock_session.commit.assert_called()


def test_calculate_scope_hash_consistency(resource_manager):
    """Test that same scope name+version produce same hash."""
    hash1 = resource_manager.calculate_scope_hash("io.opentelemetry.sdk", "1.0.0")
    hash2 = resource_manager.calculate_scope_hash("io.opentelemetry.sdk", "1.0.0")

    assert hash1 == hash2
    assert len(hash1) == 64


def test_calculate_scope_hash_different_values(resource_manager):
    """Test that different scope values produce different hashes."""
    hash1 = resource_manager.calculate_scope_hash("io.opentelemetry.sdk", "1.0.0")
    hash2 = resource_manager.calculate_scope_hash("io.opentelemetry.sdk", "2.0.0")  # Different version

    assert hash1 != hash2


def test_get_or_create_scope_cache_hit(resource_manager):
    """Test scope lookup from cache."""
    name = "my.library"
    version = "1.0.0"
    scope_hash = resource_manager.calculate_scope_hash(name, version)

    # Pre-populate cache
    resource_manager._scope_cache[scope_hash] = 100

    # Mock last_seen update
    mock_scope = MagicMock()
    mock_session = resource_manager.session
    mock_result = MagicMock()
    mock_result.first.return_value = mock_scope
    mock_session.exec.return_value = mock_result

    scope_id, created, returned_hash = resource_manager.get_or_create_scope(name, version)

    assert scope_id == 100
    assert created is False
    assert returned_hash == scope_hash


def test_get_or_create_scope_db_hit(resource_manager, mock_session):
    """Test scope lookup from database (cache miss)."""
    name = "my.library"
    version = "1.0.0"
    scope_hash = resource_manager.calculate_scope_hash(name, version)

    # Mock database response
    mock_scope = OtelScopesDim(
        scope_id=200,
        scope_hash=scope_hash,
        name=name,
        version=version,
        attributes={},
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )

    # First query: find existing, second query: last_seen update lookup
    mock_result1 = MagicMock()
    mock_result1.first.return_value = mock_scope
    mock_result2 = MagicMock()
    mock_result2.first.return_value = mock_scope
    mock_session.exec.side_effect = [mock_result1, mock_result2]

    scope_id, created, returned_hash = resource_manager.get_or_create_scope(name, version)

    assert scope_id == 200
    assert created is False
    assert returned_hash == scope_hash
    # Should be cached now
    assert resource_manager._scope_cache[scope_hash] == 200


def test_get_or_create_scope_create_new(resource_manager, mock_session):
    """Test creating new scope record."""
    name = "new.library"
    version = "2.0.0"
    attributes = {"key": "value"}
    scope_hash = resource_manager.calculate_scope_hash(name, version)

    # Mock: first query returns None, second query returns new scope
    mock_scope = OtelScopesDim(
        scope_id=300,
        scope_hash=scope_hash,
        name=name,
        version=version,
        attributes=attributes,
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )

    mock_result_none = MagicMock()
    mock_result_none.first.return_value = None
    mock_result_with_scope = MagicMock()
    mock_result_with_scope.first.return_value = mock_scope

    mock_session.exec.side_effect = [
        mock_result_none,  # Initial query
        MagicMock(),  # Upsert execution
        mock_result_with_scope,  # Final query
    ]

    scope_id, created, returned_hash = resource_manager.get_or_create_scope(name, version, attributes)

    assert scope_id == 300
    assert created is True
    assert returned_hash == scope_hash
    # Should be cached
    assert resource_manager._scope_cache[scope_hash] == 300
    mock_session.commit.assert_called()


def test_clear_cache(resource_manager):
    """Test clearing both resource and scope caches."""
    resource_manager._resource_cache = {"hash1": 1, "hash2": 2}
    resource_manager._scope_cache = {"hash3": 3, "hash4": 4}

    resource_manager.clear_cache()

    assert len(resource_manager._resource_cache) == 0
    assert len(resource_manager._scope_cache) == 0


def test_get_resource_cache_size(resource_manager):
    """Test getting resource cache size."""
    assert resource_manager.get_resource_cache_size() == 0

    resource_manager._resource_cache = {"hash1": 1, "hash2": 2}

    assert resource_manager.get_resource_cache_size() == 2


def test_get_scope_cache_size(resource_manager):
    """Test getting scope cache size."""
    assert resource_manager.get_scope_cache_size() == 0

    resource_manager._scope_cache = {"hash1": 1, "hash2": 2, "hash3": 3}

    assert resource_manager.get_scope_cache_size() == 3
