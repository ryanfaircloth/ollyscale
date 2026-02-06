"""Unit tests for trace_id/span_id conversion per OTLP specification.

Tests verify compliance with OpenTelemetry Protocol specification:
- trace_id: 16 bytes → 32 hex chars
- span_id: 8 bytes → 16 hex chars
- JSON encoding: base64
- Storage format: hex string (VARCHAR)

Uses make_span() and make_resource_spans() test fixtures for storage tests.
"""

import base64

from app.storage.postgres_orm_sync import PostgresStorage
from tests.fixtures import make_resource_spans, make_span


class TestTraceIdConversion:
    """Test trace_id and span_id conversion per OTLP spec."""

    def test_base64_to_hex_trace_id(self):
        """Verify base64 → hex conversion for trace_id (16 bytes → 32 hex)."""
        # 16 bytes: 0x01020304050607080901020304050607
        trace_bytes = bytes(range(1, 17))
        trace_base64 = base64.b64encode(trace_bytes).decode("ascii")

        # Should be 24 chars base64 (16 bytes * 8 bits / 6 bits per char)
        assert len(trace_base64) == 24

        # Convert to hex
        result = PostgresStorage._base64_to_hex(trace_base64)

        # Should be 32 hex chars
        assert len(result) == 32
        assert result == trace_bytes.hex()
        assert result == "0102030405060708090a0b0c0d0e0f10"

    def test_base64_to_hex_span_id(self):
        """Verify base64 → hex conversion for span_id (8 bytes → 16 hex)."""
        # 8 bytes: 0x0102030405060708
        span_bytes = bytes(range(1, 9))
        span_base64 = base64.b64encode(span_bytes).decode("ascii")

        # Should be 12 chars base64 (8 bytes * 8 bits / 6 bits per char)
        assert len(span_base64) == 12

        # Convert to hex
        result = PostgresStorage._base64_to_hex(span_base64)

        # Should be 16 hex chars
        assert len(result) == 16
        assert result == span_bytes.hex()
        assert result == "0102030405060708"

    def test_hex_passthrough_trace_id(self):
        """Verify hex trace_id (32 chars) passes through unchanged."""
        hex_trace = "0102030405060708090a0b0c0d0e0f10"

        # If already 32 hex chars, should pass through
        result = PostgresStorage._base64_to_hex(hex_trace)

        assert result == hex_trace
        assert len(result) == 32

    def test_hex_passthrough_span_id(self):
        """Verify hex span_id (16 chars) passes through unchanged."""
        hex_span = "0102030405060708"

        # If already 16 hex chars, should pass through
        result = PostgresStorage._base64_to_hex(hex_span)

        assert result == hex_span
        assert len(result) == 16

    def test_empty_string_handling(self):
        """Verify empty strings are handled gracefully."""
        assert PostgresStorage._base64_to_hex("") == ""

    def test_invalid_base64_returns_original(self):
        """Verify invalid base64 returns original string."""
        invalid = "not-valid-base64!!!"
        result = PostgresStorage._base64_to_hex(invalid)
        assert result == invalid


class TestTraceStorageWithRealOTLP:
    """Test storage with hex IDs from test fixtures.

    Tests using make_span() and make_resource_spans() fixtures verify trace ID handling.
    """

    def test_store_trace_with_hex_ids(self, postgres_storage):
        """Verify storage handles already-hex IDs (from test fixtures)."""
        trace_hex = "0102030405060708090a0b0c0d0e0f10"
        span_hex = "0102030405060708"

        span = make_span(
            trace_id=trace_hex,  # Pass hex directly
            span_id=span_hex,
            name="test-span",
        )

        resource_spans = make_resource_spans(service_name="test-service", spans=[span])

        # Store
        count = postgres_storage.store_traces([resource_spans])
        assert count == 1

        # Retrieve and verify IDs unchanged
        trace = postgres_storage.get_trace_by_id(trace_hex)

        assert trace is not None
        assert trace["trace_id"] == trace_hex
        assert trace["spans"][0]["span_id"] == span_hex

    def test_trace_search_returns_valid_ids(self, postgres_storage, time_range, pagination):
        """Verify trace search returns non-empty hex IDs."""
        # Store a trace
        trace_hex = "aabbccddeeff00112233445566778899"
        span_hex = "aabbccddeeff0011"

        span = make_span(trace_id=trace_hex, span_id=span_hex, name="search-test")

        resource_spans = make_resource_spans(spans=[span])
        postgres_storage.store_traces([resource_spans])

        # Search
        traces, _has_more, _cursor = postgres_storage.search_traces(
            time_range=time_range, filters=None, pagination=pagination
        )

        assert len(traces) > 0

        # Verify all traces have valid IDs (search returns summaries without spans)
        for trace in traces:
            assert "trace_id" in trace
            assert trace["trace_id"] != ""
            assert len(trace["trace_id"]) == 32 or trace["trace_id"] is None

        # Fetch full trace to validate span IDs
        full_trace = postgres_storage.get_trace_by_id(traces[0]["trace_id"])
        assert full_trace is not None
        assert "spans" in full_trace

        for span in full_trace["spans"]:
            assert span["span_id"] != ""
            assert len(span["span_id"]) == 16
            assert span["trace_id"] != ""
            assert len(span["trace_id"]) == 32


class TestBytesToHexConversion:
    """Test _bytes_to_hex helper for database retrieval."""

    def test_bytes_to_hex_conversion(self):
        """Verify bytes → hex conversion."""
        test_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        result = PostgresStorage._bytes_to_hex(test_bytes)
        assert result == "0102030405060708"
        assert len(result) == 16

    def test_string_passthrough(self):
        """Verify hex string passes through unchanged."""
        hex_str = "0102030405060708"
        result = PostgresStorage._bytes_to_hex(hex_str)
        assert result == hex_str

    def test_none_returns_none(self):
        """Verify None returns None."""
        assert PostgresStorage._bytes_to_hex(None) is None

    def test_empty_bytes_returns_empty_string(self):
        """Verify empty bytes returns empty string."""
        result = PostgresStorage._bytes_to_hex(b"")
        assert result == ""
