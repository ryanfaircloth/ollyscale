"""
Resource Manager

Manages OTLP resource and scope dimension records with hash-based deduplication:
- SHA-256 hash calculation from sorted attributes
- Resource/scope deduplication (same hash reuses same ID)
- service.name and service.namespace extraction for resources
- last_seen timestamp updates
- Cache for hash → ID mappings
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, select

from app.models.otlp_schema import OtelResourcesDim, OtelScopesDim

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages OTLP resource and scope dimension records.

    Provides efficient deduplication using SHA-256 hashes of attributes
    with in-memory caching.
    """

    def __init__(self, session: Session):
        """
        Initialize ResourceManager.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self._resource_cache: dict[str, int] = {}  # hash -> resource_id
        self._scope_cache: dict[str, int] = {}  # hash -> scope_id

    def calculate_resource_hash(self, attributes: dict[str, Any]) -> str:
        """
        Calculate SHA-256 hash of resource attributes.

        Attributes are sorted by key before hashing to ensure consistency.

        Args:
            attributes: Resource attributes dict

        Returns:
            SHA-256 hex digest (64 characters)
        """
        # Sort keys for consistent hashing
        sorted_attrs = dict(sorted(attributes.items()))
        # Convert to JSON string (deterministic)
        json_str = json.dumps(sorted_attrs, sort_keys=True, separators=(",", ":"))
        # Calculate SHA-256
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def _extract_service_name(self, attributes: dict[str, Any]) -> str | None:
        """
        Extract service.name from resource attributes.

        Args:
            attributes: Resource attributes dict

        Returns:
            service.name value or None
        """
        return attributes.get("service.name")

    def _extract_service_namespace(self, attributes: dict[str, Any]) -> str | None:
        """
        Extract service.namespace from resource attributes.

        Args:
            attributes: Resource attributes dict

        Returns:
            service.namespace value or None
        """
        return attributes.get("service.namespace")

    def get_or_create_resource(self, attributes: dict[str, Any]) -> tuple[int, bool, str]:
        """
        Get or create resource dimension record with deduplication.

        Args:
            attributes: Resource attributes dict (flattened, not OTLP AnyValue)

        Returns:
            Tuple of (resource_id, created, resource_hash) where:
            - resource_id: Primary key of resource dimension
            - created: True if new resource was created
            - resource_hash: SHA-256 hash of attributes
        """
        # Calculate hash
        resource_hash = self.calculate_resource_hash(attributes)

        # Check cache first
        if resource_hash in self._resource_cache:
            resource_id = self._resource_cache[resource_hash]
            # Update last_seen timestamp
            self._update_resource_last_seen(resource_id)
            return resource_id, False, resource_hash

        # Query database
        stmt = select(OtelResourcesDim).where(OtelResourcesDim.resource_hash == resource_hash)
        existing = self.session.exec(stmt).first()

        if existing:
            resource_id = existing.resource_id
            self._resource_cache[resource_hash] = resource_id
            # Update last_seen
            self._update_resource_last_seen(resource_id)
            return resource_id, False, resource_hash

        # Create new resource
        service_name = self._extract_service_name(attributes)
        service_namespace = self._extract_service_namespace(attributes)

        insert_stmt = pg_insert(OtelResourcesDim).values(
            resource_hash=resource_hash,
            service_name=service_name,
            service_namespace=service_namespace,
            attributes=attributes,  # Store full attributes as JSONB
            first_seen=datetime.now(UTC),
            last_seen=datetime.now(UTC),
        )
        # Upsert for concurrency safety
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["resource_hash"],
            set_={
                "last_seen": insert_stmt.excluded.last_seen,
                # Don't update attributes/service_name/namespace on conflict
            },
        )
        self.session.exec(upsert_stmt)
        self.session.commit()

        # Query again to get ID
        existing = self.session.exec(stmt).first()
        if existing:
            resource_id = existing.resource_id
            self._resource_cache[resource_hash] = resource_id
            return resource_id, True, resource_hash

        raise RuntimeError("Failed to create resource dimension")

    def _update_resource_last_seen(self, resource_id: int):
        """
        Update last_seen timestamp for resource.

        Args:
            resource_id: Resource dimension ID
        """
        stmt = select(OtelResourcesDim).where(OtelResourcesDim.resource_id == resource_id)
        resource = self.session.exec(stmt).first()
        if resource:
            resource.last_seen = datetime.now(UTC)
            self.session.add(resource)
            self.session.commit()

    def calculate_scope_hash(self, name: str, version: str) -> str:
        """
        Calculate SHA-256 hash of scope (name + version).

        Args:
            name: Scope name (e.g., 'io.opentelemetry.sdk')
            version: Scope version (e.g., '1.0.0')

        Returns:
            SHA-256 hex digest (64 characters)
        """
        # Combine name and version
        scope_data = {"name": name, "version": version}
        json_str = json.dumps(scope_data, sort_keys=True, separators=(",", ":"))
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def get_or_create_scope(
        self, name: str, version: str, attributes: dict[str, Any] | None = None
    ) -> tuple[int, bool, str]:
        """
        Get or create scope dimension record with deduplication.

        Args:
            name: Scope name
            version: Scope version
            attributes: Optional scope attributes (OTLP allows scope attributes)

        Returns:
            Tuple of (scope_id, created, scope_hash) where:
            - scope_id: Primary key of scope dimension
            - created: True if new scope was created
            - scope_hash: SHA-256 hash of name + version
        """
        # Calculate hash
        scope_hash = self.calculate_scope_hash(name, version)

        # Check cache first
        if scope_hash in self._scope_cache:
            scope_id = self._scope_cache[scope_hash]
            # Update last_seen timestamp
            self._update_scope_last_seen(scope_id)
            return scope_id, False, scope_hash

        # Query database
        stmt = select(OtelScopesDim).where(OtelScopesDim.scope_hash == scope_hash)
        existing = self.session.exec(stmt).first()

        if existing:
            scope_id = existing.scope_id
            self._scope_cache[scope_hash] = scope_id
            # Update last_seen
            self._update_scope_last_seen(scope_id)
            return scope_id, False, scope_hash

        # Create new scope
        insert_stmt = pg_insert(OtelScopesDim).values(
            scope_hash=scope_hash,
            name=name,
            version=version,
            attributes=attributes or {},  # Store scope attributes as JSONB
            first_seen=datetime.now(UTC),
            last_seen=datetime.now(UTC),
        )
        # Upsert for concurrency safety
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["scope_hash"],
            set_={
                "last_seen": insert_stmt.excluded.last_seen,
            },
        )
        self.session.exec(upsert_stmt)
        self.session.commit()

        # Query again to get ID
        existing = self.session.exec(stmt).first()
        if existing:
            scope_id = existing.scope_id
            self._scope_cache[scope_hash] = scope_id
            return scope_id, True, scope_hash

        raise RuntimeError("Failed to create scope dimension")

    def _update_scope_last_seen(self, scope_id: int):
        """
        Update last_seen timestamp for scope.

        Args:
            scope_id: Scope dimension ID
        """
        stmt = select(OtelScopesDim).where(OtelScopesDim.scope_id == scope_id)
        scope = self.session.exec(stmt).first()
        if scope:
            scope.last_seen = datetime.now(UTC)
            self.session.add(scope)
            self.session.commit()

    def clear_cache(self):
        """Clear both resource and scope caches (useful for testing)."""
        self._resource_cache.clear()
        self._scope_cache.clear()

    def get_resource_cache_size(self) -> int:
        """Get current resource cache size (useful for monitoring)."""
        return len(self._resource_cache)

    def get_scope_cache_size(self) -> int:
        """Get current scope cache size (useful for monitoring)."""
        return len(self._scope_cache)
