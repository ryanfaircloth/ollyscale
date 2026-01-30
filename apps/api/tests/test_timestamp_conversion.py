"""Unit tests for timestamp conversion utilities."""

from app.storage.postgres_orm_sync import (
    _calculate_duration_seconds,
    _nanoseconds_to_timestamp_nanos,
    _timestamp_nanos_to_nanoseconds,
    _timestamp_to_rfc3339,
)


class TestTimestampConversion:
    """Test timestamp conversion."""

    def test_nanoseconds_to_timestamp_nanos_basic(self):
        """Test basic conversion."""
        ns = 1769362245123456789
        timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(ns)

        assert timestamp.year == 2026
        assert timestamp.microsecond == 123456
        assert nanos_fraction == 789

    def test_roundtrip(self):
        """Test roundtrip preserves precision."""
        original_ns = 1769362245123456789
        timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(original_ns)
        result_ns = _timestamp_nanos_to_nanoseconds(timestamp, nanos_fraction)
        assert result_ns == original_ns

    def test_timestamp_to_rfc3339(self):
        """Test RFC3339 generation."""
        ns = 1769362245123456789
        timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(ns)
        rfc3339 = _timestamp_to_rfc3339(timestamp, nanos_fraction)
        assert rfc3339 == "2026-01-25T17:30:45.123456789Z"

    def test_duration_calculation(self):
        """Test duration calculation."""
        start_ns = 1000000000000000000
        end_ns = 1000000001000000000

        start_ts, start_nanos = _nanoseconds_to_timestamp_nanos(start_ns)
        end_ts, end_nanos = _nanoseconds_to_timestamp_nanos(end_ns)

        result = _calculate_duration_seconds(start_ts, start_nanos, end_ts, end_nanos)
        assert result == 1.0

    def test_real_world_timestamp(self):
        """Test with actual 2026 timestamp."""
        ns = 1769378244074228326
        timestamp, nanos_fraction = _nanoseconds_to_timestamp_nanos(ns)

        rfc = _timestamp_to_rfc3339(timestamp, nanos_fraction)
        assert rfc == "2026-01-25T21:57:24.074228326Z"

        result_ns = _timestamp_nanos_to_nanoseconds(timestamp, nanos_fraction)
        assert result_ns == ns
