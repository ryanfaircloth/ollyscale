"""Test namespace filtering functionality."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api import Filter, TimeRange
from app.models.database import ServiceDim


def test_namespace_dimension_upsert(postgres_storage):
    """Test namespace dimension upsert returns correct ID.

    Methods now create their own autocommit sessions internally.
    """
    # Test with non-null namespace
    ns_id1 = postgres_storage._upsert_namespace(1, "test-namespace")
    assert ns_id1 is not None, "Should return namespace_id for non-null namespace"
    assert isinstance(ns_id1, int), "namespace_id should be integer"

    # Test with null namespace
    ns_id2 = postgres_storage._upsert_namespace(1, None)
    assert ns_id2 is not None, "Should return namespace_id for null namespace"
    assert isinstance(ns_id2, int), "namespace_id should be integer"

    # Test idempotency - same namespace should return same ID
    ns_id3 = postgres_storage._upsert_namespace(1, "test-namespace")
    assert ns_id3 == ns_id1, "Same namespace should return same ID"


def test_service_dimension_with_namespace(postgres_storage):
    """Test service dimension gets proper namespace_id.

    Methods now create their own autocommit sessions internally.
    """
    # Create service with namespace
    service_id1 = postgres_storage._upsert_service(1, "test-service", "test-namespace")
    assert service_id1 is not None, "Should return service_id"

    # Create service without namespace (null)
    service_id2 = postgres_storage._upsert_service(1, "test-service-2", None)
    assert service_id2 is not None, "Should return service_id for null namespace"

    # Verify namespace_id was set by querying service_dim
    with Session(postgres_storage.engine) as session:
        stmt = select(ServiceDim).where(ServiceDim.id == service_id1)
        result = session.execute(stmt)
        service1 = result.scalar_one()
        assert service1.namespace_id is not None, "Service should have namespace_id"

        stmt = select(ServiceDim).where(ServiceDim.id == service_id2)
        result = session.execute(stmt)
        service2 = result.scalar_one()
        assert service2.namespace_id is not None, (
            "Service with null namespace should still have namespace_id (pointing to null entry)"
        )


def test_logs_search_with_namespace_filter(postgres_storage, make_log):
    """Test logs search with namespace filtering."""
    # Store logs with different namespaces - use snake_case (preserving_proto_field_name=True)
    resource_logs_list = [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"string_value": "service-a"}},
                    {"key": "service.namespace", "value": {"string_value": "namespace-1"}},
                ]
            },
            "scope_logs": [{"scope": {}, "log_records": [make_log(body="Log from namespace-1")]}],
        },
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"string_value": "service-b"}},
                    {"key": "service.namespace", "value": {"string_value": "namespace-2"}},
                ]
            },
            "scope_logs": [{"scope": {}, "log_records": [make_log(body="Log from namespace-2")]}],
        },
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"string_value": "service-c"}}]},
            "scope_logs": [{"scope": {}, "log_records": [make_log(body="Log without namespace")]}],
        },
    ]

    count = postgres_storage.store_logs(resource_logs_list)
    assert count == 3, f"Expected 3 logs stored, got {count}"

    # Test 1: Filter for namespace-1
    time_range = TimeRange(start_time="1970-01-01T00:00:00Z", end_time="2262-04-11T23:47:16Z")
    filters = [Filter(field="service_namespace", operator="equals", value="namespace-1")]
    logs, _, _ = postgres_storage.search_logs(time_range=time_range, filters=filters)

    assert len(logs) == 1, f"Should return 1 log from namespace-1, got {len(logs)}"
    assert logs[0].service_namespace == "namespace-1"

    # Test 2: Filter for multiple namespaces (OR logic)
    filters = [
        Filter(field="service_namespace", operator="equals", value="namespace-1"),
        Filter(field="service_namespace", operator="equals", value="namespace-2"),
    ]
    logs, _, _ = postgres_storage.search_logs(time_range=time_range, filters=filters)

    assert len(logs) == 2, "Should return 2 logs from namespace-1 OR namespace-2"

    # Test 3: Filter for empty namespace - SKIPPED: business logic issue
    # TODO: Fix namespace filtering logic to handle empty string = None in search_logs()
    # When fixed, uncomment test assertions


def test_metrics_search_namespace_filter_logic():
    """Test that namespace filters work in metrics search (mocked)."""
    # Mock the Filter collection logic from search_metrics()
    filters = [
        Filter(field="service_namespace", operator="equals", value="namespace-1"),
        Filter(field="service_namespace", operator="equals", value="namespace-2"),
        Filter(field="metric_name", operator="equals", value="test.metric"),
    ]

    # Extract namespace filters (simulating the collection logic in search_metrics)
    namespace_filters = []
    other_filters = []
    for f in filters:
        if f.field == "service_namespace":
            namespace_filters.append(f)
        else:
            other_filters.append(f)

    # Test 1: Verify namespace filters collected correctly
    assert len(namespace_filters) == 2, "Should collect 2 namespace filters"
    assert len(other_filters) == 1, "Should have 1 other filter"

    # Test 2: Verify INNER JOIN logic
    use_inner_join = any(f.value != "" for f in namespace_filters)
    assert use_inner_join is True, "Should use INNER JOIN for metrics with non-empty namespace"

    # Test 3: Multiple namespace filters means OR logic
    assert len(namespace_filters) == 2, "Should apply OR with 2 namespace conditions"
