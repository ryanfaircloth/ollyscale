"""
Attribute Manager

Manages OTLP attribute keys and values with promotion-based routing.

CRITICAL: Uses AUTOCOMMIT engine for key upserts to avoid deadlocks.
"""

import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.otlp_schema import AttributeKey
from app.storage.attribute_promotion_config import AttributePromotionConfig

logger = logging.getLogger(__name__)


class AttributeManager:
    """
    Manages attribute keys and storage routing for OTLP attributes.

    Uses autocommit engine for key upserts (idempotent, multi-process safe).
    Attribute value inserts use caller's session (can be transactional).
    """

    def __init__(self, autocommit_engine: Engine, config: AttributePromotionConfig):
        """
        Initialize AttributeManager.

        Args:
            autocommit_engine: SQLAlchemy engine with AUTOCOMMIT isolation level
            config: Attribute promotion configuration
        """
        self.autocommit_engine = autocommit_engine
        self.config = config
        self._key_cache: dict[str, int] = {}  # key -> key_id mapping

    def get_or_create_key_id(self, key: str) -> int:
        """
        Get or create attribute key ID with caching.

        Uses autocommit engine for idempotent upsert - safe for multi-process execution.

        Args:
            key: Attribute key name (e.g., 'service.name', 'http.status_code')

        Returns:
            Attribute key ID
        """
        # Check cache first
        if key in self._key_cache:
            return self._key_cache[key]

        # Use autocommit engine - INSERT ON CONFLICT commits immediately
        with Session(self.autocommit_engine) as session:
            stmt = (
                insert(AttributeKey)
                .values(key=key)
                .on_conflict_do_update(
                    index_elements=["key"],
                    set_={"key": insert(AttributeKey).excluded.key},  # No-op update
                )
                .returning(AttributeKey.key_id)
            )
            result = session.execute(stmt)  # ← Commits immediately!
            key_id = result.scalar_one()

        # Cache the result
        self._key_cache[key] = key_id
        return key_id

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
        parent_id: int,
        parent_table: str,
        attributes: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Store attributes with promotion-based routing.

        NOTE: This method does NOT commit - caller must commit the session.
        Attribute key upserts use autocommit (already committed).
        Attribute value inserts use autocommit session for immediate visibility.

        Args:
            signal: Signal type ('resource', 'scope', 'logs', 'spans', 'metrics')
            parent_id: Foreign key ID (resource_id, log_id, span_id, etc.)
            parent_table: Table prefix (e.g., 'otel_log_attrs', 'otel_span_attrs')
            attributes: Dict mapping key -> value (already flattened, not OTLP AnyValue)

        Returns:
            Dict of all attributes stored (for JSONB catch-all column)
        """
        all_attrs = {}

        for key, value in attributes.items():
            # Check drop list first
            if self.config.should_drop(signal, key):
                logger.debug(f"Dropping attribute {signal}.{key}")
                continue

            # Get or create key_id (uses autocommit)
            key_id = self.get_or_create_key_id(key)

            # Determine type and whether promoted
            value_type = self._infer_python_type(value)
            is_promoted = self.config.is_promoted(signal, key, value_type)

            if is_promoted:
                # Store in typed table (using autocommit for immediate visibility)
                self._store_typed_attribute(
                    parent_table=parent_table,
                    parent_id=parent_id,
                    key_id=key_id,
                    value_type=value_type,
                    value=value,
                )

            # Always add to all_attrs for potential JSONB storage
            all_attrs[key] = value

        return all_attrs

    def _infer_python_type(self, value: Any) -> str:
        """
        Infer OTLP type from Python value.

        Args:
            value: Python value

        Returns:
            One of: 'string', 'int', 'double', 'bool', 'bytes', 'other'
        """
        if isinstance(value, str):
            return "string"
        elif isinstance(value, bool):  # Check bool before int (bool is subclass of int)
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, bytes):
            return "bytes"
        else:
            return "other"

    def _store_typed_attribute(
        self,
        parent_table: str,
        parent_id: int,
        key_id: int,
        value_type: str,
        value: Any,
    ):
        """
        Store attribute in typed table.

        Uses autocommit engine for immediate visibility to other processes.

        Args:
            parent_table: Table prefix (e.g., 'otel_log_attrs')
            parent_id: FK to parent row
            key_id: FK to attribute_keys
            value_type: 'string', 'int', 'double', 'bool', 'bytes', or 'other'
            value: Attribute value
        """
        # Map to actual table name
        table_map = {
            "string": f"{parent_table}_string",
            "int": f"{parent_table}_int",
            "double": f"{parent_table}_double",
            "bool": f"{parent_table}_bool",
            "bytes": f"{parent_table}_bytes",
            "other": f"{parent_table}_other",
        }

        table_name = table_map.get(value_type)
        if not table_name:
            logger.warning(f"Unknown value type: {value_type}")
            return

        # Determine parent ID column name
        if "resource" in parent_table:
            parent_id_col = "resource_id"
        elif "scope" in parent_table:
            parent_id_col = "scope_id"
        elif "log" in parent_table:
            parent_id_col = "log_id"
        elif "span" in parent_table:
            parent_id_col = "span_id"
        elif "event" in parent_table:
            parent_id_col = "event_id"
        elif "link" in parent_table:
            parent_id_col = "link_id"
        elif "metric" in parent_table or "data_point" in parent_table:
            parent_id_col = "data_point_id"
        else:
            logger.error(f"Cannot determine parent ID column for table: {parent_table}")
            return

        # Use raw SQL for insert (table name is dynamic)
        # Uses autocommit engine for immediate commit
        with Session(self.autocommit_engine) as session:
            sql = f"""
                INSERT INTO {table_name} ({parent_id_col}, key_id, value)
                VALUES (:parent_id, :key_id, :value)
            """
            session.execute(sql, {"parent_id": parent_id, "key_id": key_id, "value": value})
            # ← Commits immediately!
