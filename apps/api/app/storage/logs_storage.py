"""
Logs Storage Implementation

Handles OTLP log record ingestion using the new schema:
- Resource/scope dimension management via ResourceManager
- Attribute promotion/storage via AttributeManager
- Log fact table insertion with trace correlation
- Integration with AttributePromotionConfig for promotion rules
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.models.otlp_schema import (
    OtelLogAttrsBool,
    OtelLogAttrsBytes,
    OtelLogAttrsDouble,
    OtelLogAttrsInt,
    OtelLogAttrsOther,
    OtelLogAttrsString,
    OtelLogsFact,
)
from app.storage.attribute_manager import AttributeManager
from app.storage.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class LogsStorage:
    """
    Manages OTLP log record storage with new schema.

    Uses DRY managers (ResourceManager, AttributeManager) for dimension
    and attribute handling.
    """

    def __init__(self, session: Session):
        """
        Initialize LogsStorage.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.resource_manager = ResourceManager(session)
        self.attribute_manager = AttributeManager(session)

        # Table class mapping for attribute routing
        self.log_attr_tables = {
            "string": OtelLogAttrsString,
            "int": OtelLogAttrsInt,
            "double": OtelLogAttrsDouble,
            "bool": OtelLogAttrsBool,
            "bytes": OtelLogAttrsBytes,
            "other": OtelLogAttrsOther,
        }

    def _flatten_otlp_attributes(self, otlp_attrs: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Convert OTLP KeyValue list to flat dict.

        OTLP format: [{"key": "service.name", "value": {"stringValue": "api"}}]
        Flat format: {"service.name": "api"}

        Args:
            otlp_attrs: List of OTLP KeyValue dicts

        Returns:
            Flattened attribute dict (key -> simple value)
        """
        flattened = {}
        for kv in otlp_attrs:
            key = kv.get("key")
            value_struct = kv.get("value", {})

            # Extract simple value from AnyValue
            if "stringValue" in value_struct:
                flattened[key] = value_struct["stringValue"]
            elif "intValue" in value_struct:
                int_val = value_struct["intValue"]
                flattened[key] = int(int_val) if isinstance(int_val, str) else int_val
            elif "doubleValue" in value_struct:
                flattened[key] = float(value_struct["doubleValue"])
            elif "boolValue" in value_struct:
                flattened[key] = bool(value_struct["boolValue"])
            elif "bytesValue" in value_struct:
                flattened[key] = value_struct["bytesValue"]
            else:
                # Complex type - store as-is
                flattened[key] = value_struct

        return flattened

    def store_logs(self, otlp_logs: dict[str, Any]) -> dict[str, Any]:
        """
        Store OTLP log records.

        OTLP structure:
        {
            "resourceLogs": [{
                "resource": {"attributes": [...]},
                "scopeLogs": [{
                    "scope": {"name": "...", "version": "..."},
                    "logRecords": [...]
                }]
            }]
        }

        Args:
            otlp_logs: OTLP ExportLogsServiceRequest dict

        Returns:
            Storage statistics (logs_stored, resources_created, etc.)
        """
        stats = {
            "logs_stored": 0,
            "resources_created": 0,
            "scopes_created": 0,
            "attributes_promoted": 0,
            "attributes_other": 0,
        }

        resource_logs_list = otlp_logs.get("resourceLogs", [])

        for resource_logs in resource_logs_list:
            # Handle resource dimension
            resource_attrs_otlp = resource_logs.get("resource", {}).get("attributes", [])
            resource_attrs_flat = self._flatten_otlp_attributes(resource_attrs_otlp)

            resource_id, created, _ = self.resource_manager.get_or_create_resource(resource_attrs_flat)
            if created:
                stats["resources_created"] += 1

            # Process scope logs
            scope_logs_list = resource_logs.get("scopeLogs", [])

            for scope_logs in scope_logs_list:
                # Handle scope dimension
                scope_info = scope_logs.get("scope", {})
                scope_name = scope_info.get("name", "")
                scope_version = scope_info.get("version", "")
                scope_attrs_otlp = scope_info.get("attributes", [])
                scope_attrs_flat = self._flatten_otlp_attributes(scope_attrs_otlp)

                scope_id, created, _ = self.resource_manager.get_or_create_scope(
                    scope_name, scope_version, scope_attrs_flat
                )
                if created:
                    stats["scopes_created"] += 1

                # Process log records
                log_records = scope_logs.get("logRecords", [])

                for log_record in log_records:
                    # Store log fact
                    self._store_log_record(log_record, resource_id, scope_id, stats)
                    stats["logs_stored"] += 1

        self.session.commit()
        return stats

    def _store_log_record(
        self,
        log_record: dict[str, Any],
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """
        Store a single log record.

        Args:
            log_record: OTLP LogRecord dict
            resource_id: Resource dimension ID
            scope_id: Scope dimension ID
            stats: Statistics dict to update

        Returns:
            log_id: Primary key of inserted log
        """
        # Extract core fields
        time_unix_nano = int(log_record.get("timeUnixNano", 0))
        observed_time_unix_nano = int(log_record.get("observedTimeUnixNano", 0))
        severity_number = int(log_record.get("severityNumber", 0))
        severity_text = log_record.get("severityText", "")
        body_value = log_record.get("body", {})
        flags = int(log_record.get("flags", 0))

        # Extract body as string (simplified - could be complex)
        if "stringValue" in body_value:
            body = body_value["stringValue"]
        else:
            body = str(body_value)  # Fallback for complex bodies

        # Trace correlation
        trace_id = log_record.get("traceId")
        span_id = log_record.get("spanId")

        # Convert trace_id/span_id to lowercase hex if present
        if trace_id:
            if isinstance(trace_id, bytes):
                trace_id = trace_id.hex()
            trace_id = trace_id.lower()

        if span_id:
            if isinstance(span_id, bytes):
                span_id = span_id.hex()
            span_id = span_id.lower()

        # Insert log fact (get ID back)
        log_fact = OtelLogsFact(
            resource_id=resource_id,
            scope_id=scope_id,
            time_unix_nano=time_unix_nano,
            observed_time_unix_nano=observed_time_unix_nano,
            severity_number=severity_number,
            severity_text=severity_text,
            body=body,
            flags=flags,
            trace_id=trace_id,
            span_id_hex=span_id,
        )
        self.session.add(log_fact)
        self.session.flush()  # Get log_id

        log_id = log_fact.log_id

        # Handle attributes
        log_attrs_otlp = log_record.get("attributes", [])
        log_attrs_anyvalue = {}  # key -> OTLP AnyValue dict

        for kv in log_attrs_otlp:
            key = kv.get("key")
            value = kv.get("value", {})
            log_attrs_anyvalue[key] = value

        # Store attributes with promotion
        promoted, other = self.attribute_manager.store_attributes(
            signal="logs",
            entity_id=log_id,
            attributes=log_attrs_anyvalue,
            table_classes=self.log_attr_tables,
        )

        stats["attributes_promoted"] += len(promoted)
        stats["attributes_other"] += len(other)

        # Store other attributes in JSONB if any
        if other:
            log_fact.attributes_other = other
            self.session.add(log_fact)

        return log_id

    def get_logs(
        self,
        start_time: int,
        end_time: int,
        severity_min: int | None = None,
        trace_id: str | None = None,
        service_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Query logs using v_otel_logs_enriched view.

        Args:
            start_time: Start time (unix nanoseconds)
            end_time: End time (unix nanoseconds)
            severity_min: Minimum severity number (optional)
            trace_id: Filter by trace ID (optional)
            service_name: Filter by service name (optional)
            limit: Max results (default 100)
            offset: Pagination offset (default 0)

        Returns:
            List of enriched log records with all attributed aggregated
        """
        # Build query with filters
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "offset": offset,
        }

        filters = [
            "time_unix_nano >= :start_time",
            "time_unix_nano <= :end_time",
        ]

        if severity_min is not None:
            filters.append("severity_number >= :severity_min")
            params["severity_min"] = severity_min

        if trace_id:
            filters.append("trace_id = :trace_id")
            params["trace_id"] = trace_id.lower()

        if service_name:
            filters.append("service_name = :service_name")
            params["service_name"] = service_name

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT
                log_id,
                time_unix_nano,
                observed_time_unix_nano,
                severity_number,
                severity_text,
                body,
                trace_id,
                span_id_hex,
                trace_flags,
                resource_id,
                resource_hash,
                resource_attributes,
                scope_id,
                scope_hash,
                scope_name,
                scope_version,
                scope_attributes,
                attributes,
                service_name,
                service_namespace,
                log_level,
                error_type,
                semantic_type
            FROM v_otel_logs_enriched
            WHERE {where_clause}
            ORDER BY time_unix_nano DESC
            LIMIT :limit
            OFFSET :offset
        """

        result = self.session.exec(text(query), params)
        rows = result.fetchall()

        # Convert rows to dicts
        logs = []
        for row in rows:
            logs.append(
                {
                    "log_id": row[0],
                    "time_unix_nano": row[1],
                    "observed_time_unix_nano": row[2],
                    "severity_number": row[3],
                    "severity_text": row[4],
                    "body": row[5],
                    "trace_id": row[6],
                    "span_id_hex": row[7],
                    "trace_flags": row[8],
                    "resource_id": row[9],
                    "resource_hash": row[10],
                    "resource_attributes": row[11],
                    "scope_id": row[12],
                    "scope_hash": row[13],
                    "scope_name": row[14],
                    "scope_version": row[15],
                    "scope_attributes": row[16],
                    "attributes": row[17],
                    "service_name": row[18],
                    "service_namespace": row[19],
                    "log_level": row[20],
                    "error_type": row[21],
                    "semantic_type": row[22],
                }
            )

        return logs
