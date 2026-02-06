"""Test service dimension functionality.

Namespace is now just a resource attribute, not a separate dimension table.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import ServiceDim


def test_service_dimension_upsert(postgres_storage):
    """Test service dimension upsert returns correct ID.

    Methods now create their own autocommit sessions internally.
    Service names are globally unique (no namespace_id).
    """
    # Create service
    service_id1 = postgres_storage._upsert_service("test-service")
    assert service_id1 is not None, "Should return service_id"

    # Test idempotency - same service should return same ID
    service_id2 = postgres_storage._upsert_service("test-service")
    assert service_id2 == service_id1, "Same service should return same ID"

    # Create another service
    service_id3 = postgres_storage._upsert_service("test-service-2")
    assert service_id3 is not None, "Should return service_id"
    assert service_id3 != service_id1, "Different services should have different IDs"

    # Verify services created in database
    with Session(postgres_storage.engine) as session:
        stmt = select(ServiceDim).where(ServiceDim.id == service_id1)
        result = session.execute(stmt)
        service1 = result.scalar_one()
        assert service1.name == "test-service"

        stmt = select(ServiceDim).where(ServiceDim.id == service_id3)
        result = session.execute(stmt)
        service2 = result.scalar_one()
        assert service2.name == "test-service-2"
