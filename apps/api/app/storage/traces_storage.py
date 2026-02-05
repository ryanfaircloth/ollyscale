"""
TracesStorage - OTLP span ingestion with correct transaction patterns.

CRITICAL: Dimension upserts use autocommit (no locks), fact inserts use transactions.

Flow:
1. Upsert resource (autocommit) → resource_id
2. Upsert scope (autocommit) → scope_id  
3. Insert span facts + attributes (transaction)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.otlp_schema import OtelSpansFact
from app.storage.attribute_manager import AttributeManager
from app.storage.attribute_promotion_config import AttributePromotionConfig
from app.storage.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class TracesStorage:
    """Storage handler for OTLP traces with multi-process safe dimension upserts."""

    def __init__(
        self,
        engine: Engine,
        autocommit_engine: Engine,
        config: AttributePromotionConfig,
    ):
        """
        Initialize traces storage.

        Args:
            engine: Transactional engine for fact inserts
            autocommit_engine: Autocommit engine for dimension upserts
            config: Attribute promotion configuration
        """
        self.engine = engine
        self.autocommit_engine = autocommit_engine
        self.config = config
        
        # Managers use autocommit engine for dimensions
        self.resource_mgr = ResourceManager(autocommit_engine)
        self.attr_mgr = AttributeManager(autocommit_engine)

    def store_traces(self, resource_spans: dict[str, Any]) -> int:
        """
        Store OTLP ResourceSpans.

        CRITICAL: Dimensions commit before facts enter transaction.

        Args:
            resource_spans: Single OTLP ResourceSpans dict

        Returns:
            Number of spans stored
        """
        # Step 1: Upsert resource OUTSIDE transaction (autocommit)
        resource_data = resource_spans.get("resource", {})
        resource_attrs = resource_data.get("attributes", [])
        dropped_attrs_count = resource_data.get("droppedAttributesCount", 0)
        
        resource_id = self.resource_mgr.get_or_create_resource(
            attributes=resource_attrs,
            dropped_attributes_count=dropped_attrs_count,
        )

        # Step 2: Process each scope's spans
        span_count = 0
        for scope_spans in resource_spans.get("scopeSpans", []):
            # Upsert scope OUTSIDE transaction (autocommit)
            scope_data = scope_spans.get("scope", {})
            scope_id = None
            if scope_data:
                scope_id = self.resource_mgr.get_or_create_scope(
                    scope=scope_data,
                    resource_id=resource_id,
                )

            # Step 3: Insert span facts IN transaction
            spans = scope_spans.get("spans", [])
            if not spans:
                continue

            with Session(self.engine) as session:
                for span in spans:
                    # Convert timestamps
                    start_time_unix_nano = span.get("startTimeUnixNano", 0)
                    end_time_unix_nano = span.get("endTimeUnixNano", 0)
                    
                    start_dt, start_nanos = self._nanos_to_timestamp(start_time_unix_nano)
                    end_dt, end_nanos = self._nanos_to_timestamp(end_time_unix_nano)

                    # Extract attributes
                    attributes = span.get("attributes", [])
                    _, unpromoted_attrs = self._process_attributes(attributes)

                    # Create span fact
                    span_fact = OtelSpansFact(
                        resource_id=resource_id,
                        scope_id=scope_id,
                        trace_id=span.get("traceId", ""),
                        span_id_hex=span.get("spanId", ""),
                        parent_span_id_hex=span.get("parentSpanId"),
                        name=span.get("name", ""),
                        kind=span.get("kind", 0),
                        start_time=start_dt,
                        start_time_nanos_fraction=start_nanos,
                        end_time=end_dt,
                        end_time_nanos_fraction=end_nanos,
                        status_code=span.get("status", {}).get("code", 0),
                        status_message=span.get("status", {}).get("message"),
                        attributes_other=unpromoted_attrs if unpromoted_attrs else None,
                        flags=span.get("flags", 0),
                    )
                    session.add(span_fact)
                
                # Flush to get span_ids
                session.flush()

                # Store promoted attributes for all spans
                for span_fact, span in zip(session.new, spans):
                    if hasattr(span_fact, "span_id"):
                        attributes = span.get("attributes", [])
                        self.attr_mgr.store_attributes(
                            signal="spans",
                            parent_id=span_fact.span_id,
                            parent_table="otel_spans_fact",
                            attributes=attributes,
                            session=session,
                        )

                session.commit()
                span_count += len(spans)

        logger.info(f"Stored {span_count} spans for resource {resource_id}")
        return span_count

    def _nanos_to_timestamp(self, unix_nano: int | None) -> tuple[datetime, int]:
        """
        Convert OTLP nanosecond timestamp to datetime + nanos fraction.

        Returns:
            (datetime, nanos_fraction) where nanos_fraction is 0-999
        """
        if unix_nano is None or unix_nano == 0:
            now = datetime.now(UTC)
            return now, 0

        # Split into seconds + nanos
        seconds = unix_nano // 1_000_000_000
        nanos = unix_nano % 1_000_000_000

        # PostgreSQL TIMESTAMP has microsecond precision
        micros = nanos // 1000
        nanos_fraction = nanos % 1000  # Remaining 0-999 nanos

        dt = datetime.fromtimestamp(seconds, tz=UTC)
        dt = dt.replace(microsecond=micros)

        return dt, nanos_fraction

    def _process_attributes(
        self, attributes: list[dict]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Split attributes into promoted and unpromoted.

        Returns:
            (promoted_dict, unpromoted_dict)
        """
        promoted = {}
        unpromoted = {}

        for attr in attributes:
            key = attr.get("key")
            value = attr.get("value", {})
            
            # Extract value by type
            extracted_value = None
            value_type = None
            
            if "stringValue" in value:
                extracted_value = value["stringValue"]
                value_type = "string"
            elif "intValue" in value:
                extracted_value = int(value["intValue"])
                value_type = "int"
            elif "doubleValue" in value:
                extracted_value = float(value["doubleValue"])
                value_type = "double"
            elif "boolValue" in value:
                extracted_value = value["boolValue"]
                value_type = "bool"
            elif "bytesValue" in value:
                extracted_value = value["bytesValue"]
                value_type = "bytes"
            else:
                # Complex types go to unpromoted
                unpromoted[key] = value
                continue

            # Check if promoted
            if self.config.is_promoted("spans", key, value_type):
                promoted[key] = extracted_value
            else:
                unpromoted[key] = extracted_value

        return promoted, unpromoted
