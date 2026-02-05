"""
Resource Manager

Manages OTLP resource and scope dimension records with hash-based deduplication.

CRITICAL: Uses AUTOCOMMIT engine to avoid deadlocks in multi-process ingestion.
Pattern copied from postgres_orm_sync.py _upsert_resource/_upsert_scope.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.otlp_schema import OtelResourcesDim, OtelScopesDim
from app.storage.attribute_manager import AttributeManager
from app.storage.attribute_promotion_config import AttributePromotionConfig

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages OTLP resource and scope dimension records.

    Uses autocommit engine for idempotent, multi-process safe upserts.
    Each upsert commits immediately - no transaction locks = no deadlocks.
    """

    def __init__(self, autocommit_engine: Engine, config: AttributePromotionConfig):
        """
        Initialize ResourceManager.

        Args:
            autocommit_engine: SQLAlchemy engine with AUTOCOMMIT isolation level
            config: Attribute promotion configuration
        """
        self.autocommit_engine = autocommit_engine
        self.config = config
        self.attr_manager = AttributeManager(autocommit_engine, config)

        self._resource_cache: dict[str, int] = {}  # hash -> resource_id
        self._scope_cache: dict[tuple[int, str], int] = {}  # (resource_id, hash) -> scope_id

        # Minimum time between last_seen updates (5 minutes default)
        self._last_seen_update_interval = timedelta(minutes=5)

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

    def calculate_scope_hash(self, scope_name: str, scope_version: str) -> str:
        """
        Calculate SHA-256 hash of scope name+version.

        Args:
            scope_name: Scope name
            scope_version: Scope version

        Returns:
            SHA-256 hex digest (64 characters)
        """
        scope_str = f"{scope_name}:{scope_version}"
        hash_obj = hashlib.sha256(scope_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def get_or_create_resource(self, resource: dict[str, Any]) -> int:
        """
        Get or create resource dimension record.

        Uses autocommit engine for idempotent upsert - safe for multi-process execution.

        Args:
            resource: OTLP Resource dict with 'attributes' key

        Returns:
            resource_id (int)
        """
        attributes = resource.get("attributes", {})
        resource_hash = self.calculate_resource_hash(attributes)

        # Check cache first
        if resource_hash in self._resource_cache:
            return self._resource_cache[resource_hash]

        # Extract denormalized fields
        service_name = attributes.get("service.name")
        service_namespace = attributes.get("service.namespace")

        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(OtelResourcesDim)
                .values(
                    resource_hash=resource_hash,
                    attributes=attributes,
                    service_name=service_name,
                    service_namespace=service_namespace,
                    first_seen=now,
                    last_seen=now,
                )
                .on_conflict_do_update(
                    index_elements=["resource_hash"],
                    set_={
                        "last_seen": case(
                            (OtelResourcesDim.last_seen < min_last_seen, now),
                            else_=OtelResourcesDim.last_seen,
                        )
                    },
                )
                .returning(OtelResourcesDim.resource_id)
            )
            result = session.execute(stmt)  # ← Commits immediately!
            resource_id = result.scalar_one()

        # Cache the result
        self._resource_cache[resource_hash] = resource_id

        # Store resource attributes (promoted + unpromoted)
        self.attr_manager.store_attributes(
            signal="resource",
            parent_id=resource_id,
            parent_table="otel_resource_attrs",
            attributes=attributes,
        )

        return resource_id

    def get_or_create_scope(self, scope: dict[str, Any], resource_id: int) -> int:
        """
        Get or create scope dimension record.

        Uses autocommit engine for idempotent upsert - safe for multi-process execution.

        Args:
            scope: OTLP InstrumentationScope dict with 'name' and 'version'
            resource_id: Parent resource ID

        Returns:
            scope_id (int)
        """
        scope_name = scope.get("name", "")
        scope_version = scope.get("version", "")
        scope_attributes = scope.get("attributes", {})

        scope_hash = self.calculate_scope_hash(scope_name, scope_version)
        cache_key = (resource_id, scope_hash)

        # Check cache first
        if cache_key in self._scope_cache:
            return self._scope_cache[cache_key]

        now = datetime.now(UTC)
        min_last_seen = now - self._last_seen_update_interval

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(OtelScopesDim)
                .values(
                    resource_id=resource_id,
                    scope_hash=scope_hash,
                    name=scope_name,
                    version=scope_version,
                    attributes=scope_attributes,
                    first_seen=now,
                    last_seen=now,
                )
                .on_conflict_do_update(
                    index_elements=["resource_id", "scope_hash"],
                    set_={
                        "last_seen": case(
                            (OtelScopesDim.last_seen < min_last_seen, now),
                            else_=OtelScopesDim.last_seen,
                        )
                    },
                )
                .returning(OtelScopesDim.scope_id)
            )
            result = session.execute(stmt)  # ← Commits immediately!
            scope_id = result.scalar_one()

        # Cache the result
        self._scope_cache[cache_key] = scope_id

        # Store scope attributes if any
        if scope_attributes:
            self.attr_manager.store_attributes(
                signal="scope",
                parent_id=scope_id,
                parent_table="otel_scope_attrs",
                attributes=scope_attributes,
            )

        return scope_id
