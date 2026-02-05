"""
Timestamp Conversion Utilities

Handles conversion between OTLP unix nanoseconds and PostgreSQL timestamp+nanos_fraction pattern.

PostgreSQL TIMESTAMP WITH TIME ZONE has microsecond precision (6 digits).
To preserve full nanosecond precision, we store:
- timestamp: TIMESTAMP WITH TIME ZONE (seconds + microseconds)
- nanos_fraction: SMALLINT (0-999, remaining nanoseconds)

Examples:
    unix_nano = 1234567890123456789
    → timestamp = 2009-02-13 23:31:30.123456+00:00
    → nanos_fraction = 789

    timestamp = 2009-02-13 23:31:30.123456+00:00
    nanos_fraction = 789
    → unix_nano = 1234567890123456789
"""

from datetime import UTC, datetime


def unix_nano_to_timestamp_and_fraction(unix_nano: int) -> tuple[datetime, int]:
    """
    Convert OTLP unix nanoseconds to (timestamp, nanos_fraction).

    Args:
        unix_nano: Nanoseconds since Unix epoch

    Returns:
        Tuple of (timestamp with microsecond precision, remaining 0-999 nanos)

    Example:
        >>> unix_nano_to_timestamp_and_fraction(1234567890123456789)
        (datetime(2009, 2, 13, 23, 31, 30, 123456, tzinfo=timezone.utc), 789)
    """
    if unix_nano == 0:
        # Return epoch with 0 nanos
        return datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=UTC), 0

    # Split into microseconds (which datetime supports) and remaining nanos
    total_micros = unix_nano // 1000
    nanos_fraction = unix_nano % 1000

    # Convert microseconds to seconds (float) for datetime
    seconds_with_micros = total_micros / 1_000_000

    # Create datetime (automatically has microsecond precision)
    timestamp = datetime.fromtimestamp(seconds_with_micros, tz=UTC)

    return timestamp, nanos_fraction


def timestamp_and_fraction_to_unix_nano(timestamp: datetime, nanos_fraction: int) -> int:
    """
    Convert (timestamp, nanos_fraction) back to OTLP unix nanoseconds.

    Args:
        timestamp: DateTime with timezone (microsecond precision)
        nanos_fraction: Remaining nanoseconds (0-999)

    Returns:
        Unix nanoseconds

    Example:
        >>> ts = datetime(2009, 2, 13, 23, 31, 30, 123456, tzinfo=timezone.utc)
        >>> timestamp_and_fraction_to_unix_nano(ts, 789)
        1234567890123456789
    """
    # Get total microseconds from epoch
    total_micros = int(timestamp.timestamp() * 1_000_000)

    # Convert to nanoseconds and add remaining nanos
    unix_nano = (total_micros * 1000) + nanos_fraction

    return unix_nano
