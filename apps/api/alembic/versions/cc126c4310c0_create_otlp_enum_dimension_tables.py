"""create otlp enum dimension tables

Revision ID: cc126c4310c0
Revises: 44ca99640ec5
Create Date: 2026-02-04 15:25:23.087616

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc126c4310c0"
down_revision: str | Sequence[str] | None = "44ca99640ec5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create OTLP enum dimension tables.

    These tables provide self-documenting schema for OTLP enum types,
    enable human-readable queries via JOINs, and give the query optimizer
    exact cardinality information for better query planning.
    """

    # span_kinds - OTLP SpanKind enum (6 values)
    op.execute("""
        CREATE TABLE span_kinds (
            kind_id SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    op.execute("""
        INSERT INTO span_kinds (kind_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified span kind'),
            (1, 'INTERNAL', 'Internal operation within an application'),
            (2, 'SERVER', 'Server-side handling of synchronous RPC or HTTP request'),
            (3, 'CLIENT', 'Client-side call to remote service'),
            (4, 'PRODUCER', 'Parent of asynchronous message sent to broker'),
            (5, 'CONSUMER', 'Child of asynchronous message received from broker')
    """)

    # status_codes - OTLP StatusCode enum (3 values)
    op.execute("""
        CREATE TABLE status_codes (
            status_code_id SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    op.execute("""
        INSERT INTO status_codes (status_code_id, name, description) VALUES
            (0, 'UNSET', 'The default status'),
            (1, 'OK', 'The operation completed successfully'),
            (2, 'ERROR', 'The operation contains an error')
    """)

    # log_severity_numbers - OTLP SeverityNumber enum (25 values)
    op.execute("""
        CREATE TABLE log_severity_numbers (
            severity_number SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            display_order SMALLINT NOT NULL
        )
    """)
    op.execute("""
        INSERT INTO log_severity_numbers (severity_number, name, description, display_order) VALUES
            (0, 'UNSPECIFIED', 'Unspecified severity', 0),
            (1, 'TRACE', 'Trace level', 1),
            (2, 'TRACE2', 'Trace level 2', 2),
            (3, 'TRACE3', 'Trace level 3', 3),
            (4, 'TRACE4', 'Trace level 4', 4),
            (5, 'DEBUG', 'Debug level', 5),
            (6, 'DEBUG2', 'Debug level 2', 6),
            (7, 'DEBUG3', 'Debug level 3', 7),
            (8, 'DEBUG4', 'Debug level 4', 8),
            (9, 'INFO', 'Informational', 9),
            (10, 'INFO2', 'Informational 2', 10),
            (11, 'INFO3', 'Informational 3', 11),
            (12, 'INFO4', 'Informational 4', 12),
            (13, 'WARN', 'Warning', 13),
            (14, 'WARN2', 'Warning 2', 14),
            (15, 'WARN3', 'Warning 3', 15),
            (16, 'WARN4', 'Warning 4', 16),
            (17, 'ERROR', 'Error', 17),
            (18, 'ERROR2', 'Error 2', 18),
            (19, 'ERROR3', 'Error 3', 19),
            (20, 'ERROR4', 'Error 4', 20),
            (21, 'FATAL', 'Fatal', 21),
            (22, 'FATAL2', 'Fatal 2', 22),
            (23, 'FATAL3', 'Fatal 3', 23),
            (24, 'FATAL4', 'Fatal 4', 24)
    """)

    # log_body_types - OTLP AnyValue type enum (8 values)
    op.execute("""
        CREATE TABLE log_body_types (
            body_type_id SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)
    op.execute("""
        INSERT INTO log_body_types (body_type_id, name) VALUES
            (0, 'EMPTY'),
            (1, 'STRING'),
            (2, 'INT'),
            (3, 'DOUBLE'),
            (4, 'BOOL'),
            (5, 'BYTES'),
            (6, 'ARRAY'),
            (7, 'KVLIST')
    """)

    # metric_types - OTLP MetricType enum (5 values)
    op.execute("""
        CREATE TABLE metric_types (
            metric_type_id SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    op.execute("""
        INSERT INTO metric_types (metric_type_id, name, description) VALUES
            (1, 'GAUGE', 'Gauge metric - instantaneous measurement'),
            (2, 'SUM', 'Sum metric - cumulative or delta aggregation'),
            (3, 'HISTOGRAM', 'Histogram - distribution with fixed buckets'),
            (4, 'EXPONENTIAL_HISTOGRAM', 'Exponential histogram - distribution with exponential buckets'),
            (5, 'SUMMARY', 'Summary - quantiles over sliding time window')
    """)

    # aggregation_temporalities - OTLP AggregationTemporality enum (3 values)
    op.execute("""
        CREATE TABLE aggregation_temporalities (
            temporality_id SMALLINT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    op.execute("""
        INSERT INTO aggregation_temporalities (temporality_id, name, description) VALUES
            (0, 'UNSPECIFIED', 'Unspecified temporality'),
            (1, 'DELTA', 'Delta aggregation - value since last export'),
            (2, 'CUMULATIVE', 'Cumulative aggregation - value since start')
    """)


def downgrade() -> None:
    """Drop OTLP enum dimension tables."""
    op.execute("DROP TABLE IF EXISTS aggregation_temporalities CASCADE")
    op.execute("DROP TABLE IF EXISTS metric_types CASCADE")
    op.execute("DROP TABLE IF EXISTS log_body_types CASCADE")
    op.execute("DROP TABLE IF EXISTS log_severity_numbers CASCADE")
    op.execute("DROP TABLE IF EXISTS status_codes CASCADE")
    op.execute("DROP TABLE IF EXISTS span_kinds CASCADE")
