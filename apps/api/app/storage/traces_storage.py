"""
Traces Storage Implementation

Handles OTLP trace/span record ingestion using the new schema:
- Resource/scope dimension management via ResourceManager
- Attribute promotion/storage via AttributeManager
- Span fact table insertion with parent-child relationships
- Span events and links storage
- Integration with AttributePromotionConfig for promotion rules
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.models.otlp_schema import (
    OtelSpanAttrsBool,
    OtelSpanAttrsBytes,
    OtelSpanAttrsDouble,
    OtelSpanAttrsInt,
    OtelSpanAttrsOther,
    OtelSpanAttrsString,
    OtelSpansFact,
)
from app.storage.attribute_manager import AttributeManager
from app.storage.resource_manager import ResourceManager
from app.utils.timestamp_utils import unix_nano_to_timestamp_and_fraction

logger = logging.getLogger(__name__)


class TracesStorage:
    """
    Manages OTLP trace/span record storage with new schema.

    Uses DRY managers (ResourceManager, AttributeManager) for dimension
    and attribute handling.
    """

    def __init__(self, session: Session):
        """
        Initialize TracesStorage.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.resource_manager = ResourceManager(session)
        self.attribute_manager = AttributeManager(session)

        # Table class mapping for attribute routing
        self.span_attr_tables = {
            "string": OtelSpanAttrsString,
            "int": OtelSpanAttrsInt,
            "double": OtelSpanAttrsDouble,
            "bool": OtelSpanAttrsBool,
            "bytes": OtelSpanAttrsBytes,
            "other": OtelSpanAttrsOther,
        }

    def _flatten_otlp_attributes(self, otlp_attrs: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Convert OTLP KeyValue list to flat dict.

        OTLP format: [{"key": "http.method", "value": {"stringValue": "GET"}}]
        Flat format: {"http.method": "GET"}

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

    def store_traces(self, resource_spans: dict[str, Any]) -> dict[str, Any]:
        """
        Store OTLP trace records from a single ResourceSpans entry.

        Args:
            resource_spans: Single OTLP ResourceSpans dict with structure:
                {
                    "resource": {"attributes": [...]},
                    "scopeSpans": [{
                        "scope": {"name": "...", "version": "..."},
                        "spans": [...]
                    }]
                }

        Returns:
            Storage statistics (spans_stored, resources_created, etc.)
        """
        stats = {
            "spans_stored": 0,
            "resources_created": 0,
            "scopes_created": 0,
            "attributes_promoted": 0,
            "attributes_other": 0,
            "events_stored": 0,
            "links_stored": 0,
        }

        # Handle resource dimension
        resource_attrs_otlp = resource_spans.get("resource", {}).get("attributes", [])
        resource_attrs_flat = self._flatten_otlp_attributes(resource_attrs_otlp)

        resource_id, created, _ = self.resource_manager.get_or_create_resource(resource_attrs_flat)
        if created:
            stats["resources_created"] += 1

        # Process scope spans
        scope_spans_list = resource_spans.get("scopeSpans", [])

        for scope_spans in scope_spans_list:
            # Handle scope dimension
            scope_info = scope_spans.get("scope", {})
            scope_name = scope_info.get("name", "")
            scope_version = scope_info.get("version", "")
            scope_attrs_otlp = scope_info.get("attributes", [])
            scope_attrs_flat = self._flatten_otlp_attributes(scope_attrs_otlp)

            scope_id, created, _ = self.resource_manager.get_or_create_scope(
                scope_name, scope_version, scope_attrs_flat
            )
            if created:
                stats["scopes_created"] += 1

            # Process spans
            spans = scope_spans.get("spans", [])

            for span in spans:
                # Store span fact
                self._store_span(span, resource_id, scope_id, stats)
                stats["spans_stored"] += 1

        return stats

    def _store_span(
        self,
        span: dict[str, Any],
        resource_id: int,
        scope_id: int,
        stats: dict[str, Any],
    ) -> int:
        """
        Store a single span record.

        Args:
            span: OTLP Span dict
            resource_id: Resource dimension ID
            scope_id: Scope dimension ID
            stats: Statistics dict to update

        Returns:
            span_id: Primary key of inserted span
        """
        # Extract core fields
        trace_id = span.get("traceId")
        span_id_hex = span.get("spanId")
        parent_span_id_hex = span.get("parentSpanId")
        name = span.get("name", "")
        kind = span.get("kind", 0)
        start_time_unix_nano = int(span.get("startTimeUnixNano", 0))
        end_time_unix_nano = int(span.get("endTimeUnixNano", 0))
        flags = int(span.get("flags", 0))

        # Convert unix_nano to timestamp+nanos_fraction
        start_time, start_time_nanos_fraction = unix_nano_to_timestamp_and_fraction(start_time_unix_nano)
        end_time, end_time_nanos_fraction = unix_nano_to_timestamp_and_fraction(end_time_unix_nano)

        # Convert IDs to lowercase hex if present
        if trace_id:
            if isinstance(trace_id, bytes):
                trace_id = trace_id.hex()
            trace_id = trace_id.lower()

        if span_id_hex:
            if isinstance(span_id_hex, bytes):
                span_id_hex = span_id_hex.hex()
            span_id_hex = span_id_hex.lower()

        if parent_span_id_hex:
            if isinstance(parent_span_id_hex, bytes):
                parent_span_id_hex = parent_span_id_hex.hex()
            parent_span_id_hex = parent_span_id_hex.lower()

        # Status
        status = span.get("status", {})
        status_code = status.get("code", 0)
        status_message = status.get("message", "")

        # Insert span fact (get ID back)
        span_fact = OtelSpansFact(
            resource_id=resource_id,
            scope_id=scope_id,
            trace_id=trace_id,
            span_id_hex=span_id_hex,
            parent_span_id_hex=parent_span_id_hex,
            name=name,
            kind=kind,
            start_time=start_time,
            start_time_nanos_fraction=start_time_nanos_fraction,
            end_time=end_time,
            end_time_nanos_fraction=end_time_nanos_fraction,
            status_code=status_code,
            status_message=status_message,
            flags=flags,
        )
        self.session.add(span_fact)
        self.session.flush()  # Get span_id

        span_pk_id = span_fact.span_id

        # Handle attributes
        span_attrs_otlp = span.get("attributes", [])
        span_attrs_anyvalue = {}  # key -> OTLP AnyValue dict

        for kv in span_attrs_otlp:
            key = kv.get("key")
            value = kv.get("value", {})
            span_attrs_anyvalue[key] = value

        # Store attributes with promotion
        promoted, other = self.attribute_manager.store_attributes(
            signal="spans",
            entity_id=span_pk_id,
            attributes=span_attrs_anyvalue,
            table_classes=self.span_attr_tables,
        )

        stats["attributes_promoted"] += len(promoted)
        stats["attributes_other"] += len(other)

        # Store other attributes in JSONB if any
        if other:
            span_fact.attributes_other = other
            self.session.add(span_fact)

        # TODO: Store span events
        # TODO: Store span links

        return span_pk_id

    def get_traces(
        self,
        start_time: int,
        end_time: int,
        service_name: str | None = None,
        min_duration: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Query traces (distinct trace_ids with aggregated metadata).

        Args:
            start_time: Start time (unix nanoseconds)
            end_time: End time (unix nanoseconds)
            service_name: Filter by service name (optional)
            min_duration: Minimum trace duration in nanoseconds (optional)
            limit: Max results (default 100)
            offset: Pagination offset (default 0)

        Returns:
            List of trace summaries with span counts and duration
        """
        # Build query with filters
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "offset": offset,
        }

        filters = [
            "start_time_unix_nano >= :start_time",
            "start_time_unix_nano <= :end_time",
        ]

        if service_name:
            filters.append("service_name = :service_name")
            params["service_name"] = service_name

        if min_duration is not None:
            filters.append("(end_time_unix_nano - start_time_unix_nano) >= :min_duration")
            params["min_duration"] = min_duration

        where_clause = " AND ".join(filters)

        # Query for distinct traces with aggregation
        query = f"""
            WITH trace_summary AS (
                SELECT
                    trace_id,
                    MIN(start_time_unix_nano) as trace_start,
                    MAX(end_time_unix_nano) as trace_end,
                    COUNT(*) as span_count,
                    service_name
                FROM v_otel_spans_enriched
                WHERE {where_clause}
                GROUP BY trace_id, service_name
            )
            SELECT
                trace_id,
                trace_start,
                trace_end,
                (trace_end - trace_start) as duration,
                span_count,
                service_name
            FROM trace_summary
            ORDER BY trace_start DESC
            LIMIT :limit
            OFFSET :offset
        """

        result = self.session.exec(text(query), params)
        rows = result.fetchall()

        # Convert rows to dicts
        traces = []
        for row in rows:
            traces.append(
                {
                    "trace_id": row[0],
                    "trace_start": row[1],
                    "trace_end": row[2],
                    "duration": row[3],
                    "span_count": row[4],
                    "service_name": row[5],
                }
            )

        return traces

    def get_trace_spans(self, trace_id: str) -> list[dict[str, Any]]:
        """
        Get all spans for a trace with full details.

        Args:
            trace_id: Trace ID (32-char hex)

        Returns:
            List of enriched span records with parent-child relationships
        """
        query = """
            SELECT
                span_id,
                trace_id,
                span_id_hex,
                parent_span_id_hex,
                name,
                kind,
                start_time_unix_nano,
                end_time_unix_nano,
                status_code,
                status_message,
                resource_id,
                resource_attributes,
                scope_id,
                scope_name,
                scope_version,
                attributes,
                service_name,
                semantic_type
            FROM v_otel_spans_enriched
            WHERE trace_id = :trace_id
            ORDER BY start_time_unix_nano ASC
        """

        result = self.session.exec(text(query), {"trace_id": trace_id.lower()})
        rows = result.fetchall()

        # Convert rows to dicts
        spans = []
        for row in rows:
            spans.append(
                {
                    "span_id": row[0],
                    "trace_id": row[1],
                    "span_id_hex": row[2],
                    "parent_span_id_hex": row[3],
                    "name": row[4],
                    "kind": row[5],
                    "start_time_unix_nano": row[6],
                    "end_time_unix_nano": row[7],
                    "duration": row[7] - row[6],
                    "status_code": row[8],
                    "status_message": row[9],
                    "resource_id": row[10],
                    "resource_attributes": row[11],
                    "scope_id": row[12],
                    "scope_name": row[13],
                    "scope_version": row[14],
                    "attributes": row[15],
                    "service_name": row[16],
                    "semantic_type": row[17],
                }
            )

        return spans
