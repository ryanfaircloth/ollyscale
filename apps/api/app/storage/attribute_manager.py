"""
Attribute Manager

Manages OTLP attribute keys and values with promotion-based routing:
- Key deduplication (attribute_keys table) with caching
- Type-specific storage routing (string/int/double/bool/bytes/other tables)
- Integration with AttributePromotionConfig for promotion/drop decisions
- Efficient batch operations
"""

import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, select

from app.models.otlp_schema import AttributeKey
from app.storage.attribute_promotion_config import get_attribute_promotion_config

logger = logging.getLogger(__name__)


class AttributeManager:
    """
    Manages attribute keys and storage routing for OTLP attributes.

    Provides efficient key deduplication with caching and type-aware storage
    routing based on promotion configuration.
    """

    def __init__(self, session: Session):
        """
        Initialize AttributeManager.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.config = get_attribute_promotion_config()
        self._key_cache: dict[str, int] = {}  # key -> key_id mapping

    def get_or_create_key_id(self, key: str) -> int:
        """
        Get or create attribute key ID with caching.

        Args:
            key: Attribute key name (e.g., 'service.name', 'http.status_code')

        Returns:
            Attribute key ID
        """
        # Check cache first
        if key in self._key_cache:
            return self._key_cache[key]

        # Query database
        stmt = select(AttributeKey).where(AttributeKey.key == key)
        existing = self.session.exec(stmt).first()

        if existing:
            key_id = existing.key_id
            self._key_cache[key] = key_id
            return key_id

        # Insert new key (upsert for concurrency safety)
        insert_stmt = pg_insert(AttributeKey).values(key=key)
        upsert_stmt = insert_stmt.on_conflict_do_update(index_elements=["key"], set_={"key": insert_stmt.excluded.key})
        self.session.exec(upsert_stmt)
        self.session.commit()

        # Query again to get ID
        existing = self.session.exec(stmt).first()
        if existing:
            key_id = existing.key_id
            self._key_cache[key] = key_id
            return key_id

        raise RuntimeError(f"Failed to create attribute key: {key}")

    def _extract_type_and_value(self, otlp_any_value: dict[str, Any]) -> tuple[str | None, Any | None]:
        """
        Extract type and value from OTLP AnyValue structure.

        OTLP AnyValue format:
        {
            "stringValue": "...",    # XOR
            "intValue": 123,         # XOR
            "doubleValue": 1.23,     # XOR
            "boolValue": true,       # XOR
            "bytesValue": "base64",  # XOR
            "arrayValue": {...},     # XOR (stored as other)
            "kvlistValue": {...}     # XOR (stored as other)
        }

        Args:
            otlp_any_value: OTLP AnyValue dict

        Returns:
            Tuple of (value_type, value) where value_type is one of:
            'string', 'int', 'double', 'bool', 'bytes', 'other', None
        """
        if "stringValue" in otlp_any_value:
            return "string", otlp_any_value["stringValue"]
        elif "intValue" in otlp_any_value:
            # OTLP intValue can be string like "123" or int 123
            int_val = otlp_any_value["intValue"]
            return "int", int(int_val) if isinstance(int_val, str) else int_val
        elif "doubleValue" in otlp_any_value:
            return "double", float(otlp_any_value["doubleValue"])
        elif "boolValue" in otlp_any_value:
            return "bool", bool(otlp_any_value["boolValue"])
        elif "bytesValue" in otlp_any_value:
            return "bytes", otlp_any_value["bytesValue"]  # Base64 string
        elif "arrayValue" in otlp_any_value or "kvlistValue" in otlp_any_value:
            # Complex types stored as JSONB
            return "other", otlp_any_value
        else:
            logger.warning(f"Unknown AnyValue structure: {otlp_any_value}")
            return None, None

    def store_attributes(
        self,
        signal: str,
        entity_id: int,
        attributes: dict[str, dict[str, Any]],
        table_classes: dict[str, type],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Store attributes with promotion-based routing.

        Args:
            signal: Signal type ('resource', 'scope', 'logs', 'spans', 'metrics')
            entity_id: Foreign key ID (resource_id, log_id, span_id, etc.)
            attributes: Dict mapping key -> OTLP AnyValue
            table_classes: Dict mapping type -> SQLModel class
                          {'string': OtelLogAttrsString, 'int': OtelLogAttrsInt, ...}

        Returns:
            Tuple of (promoted_attrs, other_attrs) where:
            - promoted_attrs: Dict of key -> value for promoted attributes (by type)
            - other_attrs: Dict of key -> value for JSONB storage
        """
        promoted_attrs: dict[str, Any] = {}
        other_attrs: dict[str, Any] = {}

        for key, any_value in attributes.items():
            # Check drop list first
            if self.config.should_drop(key):
                logger.debug(f"Dropping attribute: {key}")
                continue

            # Extract type and value
            value_type, value = self._extract_type_and_value(any_value)
            if value_type is None:
                continue

            # Check if promoted
            if self.config.is_promoted(signal, key, value_type):
                # Store in dedicated typed table
                key_id = self.get_or_create_key_id(key)

                if value_type == "other":
                    # Special case: other goes to JSONB table but still "promoted"
                    table_class = table_classes.get("other")
                    if table_class:
                        record = table_class(
                            **{
                                f"{signal}_id" if signal != "logs" else "log_id": entity_id,
                                "key_id": key_id,
                                "value": value,
                            }
                        )
                        self.session.add(record)
                else:
                    # Store in typed table
                    table_class = table_classes.get(value_type)
                    if table_class:
                        record = table_class(
                            **{
                                f"{signal}_id" if signal != "logs" else "log_id": entity_id,
                                "key_id": key_id,
                                "value": value,
                            }
                        )
                        self.session.add(record)

                promoted_attrs[key] = value
            else:
                # Store in JSONB catch-all
                other_attrs[key] = value

        return promoted_attrs, other_attrs

    def get_attributes(self, entity_id: int, signal: str, table_classes: dict[str, type]) -> dict[str, Any]:
        """
        Retrieve all attributes for an entity (promoted + other).

        Args:
            entity_id: Foreign key ID (log_id, span_id, etc.)
            signal: Signal type ('logs', 'spans', etc.)
            table_classes: Dict mapping type -> SQLModel class

        Returns:
            Dict of all attributes (key -> value)
        """
        attributes: dict[str, Any] = {}

        # Query each typed table
        for value_type, table_class in table_classes.items():
            if value_type == "other":
                continue  # Handle separately

            fk_column = f"{signal}_id" if signal != "logs" else "log_id"  # Adjust for model naming
            stmt = (
                select(table_class, AttributeKey)
                .join(AttributeKey, table_class.key_id == AttributeKey.key_id)
                .where(getattr(table_class, fk_column) == entity_id)
            )
            results = self.session.exec(stmt).all()

            for record, key in results:
                attributes[key.key] = record.value

        # Query JSONB other table
        other_table = table_classes.get("other")
        if other_table:
            fk_column = f"{signal}_id" if signal != "logs" else "log_id"
            stmt = (
                select(other_table, AttributeKey)
                .join(AttributeKey, other_table.key_id == AttributeKey.key_id)
                .where(getattr(other_table, fk_column) == entity_id)
            )
            results = self.session.exec(stmt).all()

            for record, key in results:
                attributes[key.key] = record.value

        return attributes

    def clear_cache(self):
        """Clear the key ID cache (useful for testing)."""
        self._key_cache.clear()

    def get_cache_size(self) -> int:
        """Get current cache size (useful for monitoring)."""
        return len(self._key_cache)
