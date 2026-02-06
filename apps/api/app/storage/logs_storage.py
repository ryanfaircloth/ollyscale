"""
LogsStorage - OTLP log ingestion with correct transaction patterns.

CRITICAL: Dimension upserts use autocommit (no locks), fact inserts use transactions.

Flow:
1. Upsert resource (autocommit) → resource_id
2. Upsert scope (autocommit) → scope_id
3. Insert log facts + attributes (transaction)
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.otlp_schema import OtelLogsFact
from app.storage.attribute_manager import AttributeManager
from app.storage.attribute_promotion_config import AttributePromotionConfig
from app.storage.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class LogsStorage:
    """Storage handler for OTLP logs with multi-process safe dimension upserts."""

    def __init__(
        self,
        engine: Engine,
        autocommit_engine: Engine,
        config: AttributePromotionConfig,
    ):
        """
        Initialize logs storage.

        Args:
            engine: Transactional engine for fact inserts
            autocommit_engine: Autocommit engine for dimension upserts
            config: Attribute promotion configuration
        """
        self.engine = engine
        self.autocommit_engine = autocommit_engine
        self.config = config

        # Managers use autocommit engine for dimensions
        self.resource_mgr = ResourceManager(autocommit_engine, config)
        self.attr_mgr = AttributeManager(autocommit_engine, config)

    def store_logs(self, resource_logs: dict[str, Any]) -> int:
        """
        Store OTLP ResourceLogs.

        CRITICAL: Dimensions commit before facts enter transaction.

        Args:
            resource_logs: Single OTLP ResourceLogs dict

        Returns:
            Number of log records stored
        """
        # Step 1: Upsert resource OUTSIDE transaction (autocommit)
        resource_data = resource_logs.get("resource", {})
        resource_attrs = resource_data.get("attributes", [])
        dropped_attrs_count = resource_data.get("droppedAttributesCount", 0)

        resource_id = self.resource_mgr.get_or_create_resource(
            attributes=resource_attrs,
            dropped_attributes_count=dropped_attrs_count,
        )

        # Step 2: Process each scope's logs
        log_count = 0
        for scope_logs in resource_logs.get("scopeLogs", []):
            # Upsert scope OUTSIDE transaction (autocommit)
            scope_data = scope_logs.get("scope", {})
            scope_id = None
            if scope_data:
                scope_id = self.resource_mgr.get_or_create_scope(
                    scope=scope_data,
                    resource_id=resource_id,
                )

            # Step 3: Insert log facts IN transaction
            log_records = scope_logs.get("logRecords", [])
            if not log_records:
                continue

            with Session(self.engine) as session:
                for log_record in log_records:
                    # Convert timestamps
                    time_unix_nano = log_record.get("timeUnixNano")
                    observed_time_unix_nano = log_record.get("observedTimeUnixNano", time_unix_nano)

                    time_dt, time_nanos = self._nanos_to_timestamp(time_unix_nano)
                    observed_dt, observed_nanos = self._nanos_to_timestamp(observed_time_unix_nano)

                    # Extract attributes
                    attributes = log_record.get("attributes", [])
                    _, unpromoted_attrs = self._process_attributes(attributes)

                    # Create log fact
                    log_fact = OtelLogsFact(
                        resource_id=resource_id,
                        scope_id=scope_id,
                        time=time_dt,
                        time_nanos_fraction=time_nanos,
                        observed_time=observed_dt,
                        observed_time_nanos_fraction=observed_nanos,
                        severity_number=log_record.get("severityNumber"),
                        severity_text=log_record.get("severityText"),
                        body_type_id=self._get_body_type_id(log_record.get("body", {})),
                        body=log_record.get("body"),
                        trace_id=log_record.get("traceId"),
                        span_id_hex=log_record.get("spanId"),
                        trace_flags=log_record.get("flags"),
                        attributes_other=unpromoted_attrs if unpromoted_attrs else None,
                        dropped_attributes_count=log_record.get("droppedAttributesCount", 0),
                        flags=log_record.get("flags", 0),
                    )
                    session.add(log_fact)

                # Flush to get log_ids
                session.flush()

                # Store promoted attributes for all logs
                for log_fact, log_record in zip(session.new, log_records, strict=False):
                    if hasattr(log_fact, "log_id"):
                        attributes = log_record.get("attributes", [])
                        self.attr_mgr.store_attributes(
                            signal="logs",
                            parent_id=log_fact.log_id,
                            parent_table="otel_logs_fact",
                            attributes=attributes,
                            session=session,
                        )

                session.commit()
                log_count += len(log_records)

        logger.info(f"Stored {log_count} logs for resource {resource_id}")
        return log_count

    def _nanos_to_timestamp(self, unix_nano: int | None) -> tuple[datetime, int]:
        """
        Convert OTLP nanosecond timestamp to datetime + nanos fraction.

        Returns:
            (datetime, nanos_fraction) where nanos_fraction is 0-999
        """
        if unix_nano is None:
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

    def _get_body_type_id(self, body: dict) -> int:
        """Map OTLP AnyValue type to type_id."""
        if not body:
            return 0

        # Check which field is present
        if "stringValue" in body:
            return 1
        elif "intValue" in body:
            return 2
        elif "doubleValue" in body:
            return 3
        elif "boolValue" in body:
            return 4
        elif "bytesValue" in body:
            return 5
        elif "arrayValue" in body:
            return 6
        elif "kvlistValue" in body:
            return 7

        return 0

    def _process_attributes(self, attributes: list[dict]) -> tuple[dict[str, Any], dict[str, Any]]:
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
            if self.config.is_promoted("logs", key, value_type):
                promoted[key] = extracted_value
            else:
                unpromoted[key] = extracted_value

        return promoted, unpromoted
