"""Performance benchmarking for PostgreSQL storage layer.

Tests ingestion and query performance under realistic loads.
Measures latency, throughput, and resource utilization.

Phase 12: Performance Benchmarking - validates async-to-sync migration performance.
Results normalized per vCPU core for hardware-independent comparison.
"""

import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

import pytest

from app.storage.postgres_orm_sync import PostgresStorage

# Detect CPU core count for per-core normalization
NUM_CORES = multiprocessing.cpu_count()


@pytest.fixture(scope="function")
def postgres_storage(postgres_connection_string, postgres_engine):  # noqa: ARG001
    """Create a PostgreSQL storage instance for benchmarking.

    postgres_engine dependency ensures Alembic migrations run first.
    """
    storage = PostgresStorage(connection_string=postgres_connection_string)
    storage.connect()  # Initialize database engines
    yield storage
    storage.close()


def make_resource_spans(num_spans: int, service_name: str, namespace: str = "benchmark") -> dict:
    """Generate OTLP ResourceSpans with test data."""
    now = datetime.now(UTC)
    spans = []
    for i in range(num_spans):
        timestamp = now - timedelta(milliseconds=i * 10)
        spans.append(
            {
                "trace_id": f"{i:032x}",  # 32-char hex
                "span_id": f"{i:016x}",  # 16-char hex
                "parent_span_id": None,
                "name": f"operation-{i % 10}",
                "kind": 2,  # SERVER
                "start_time_unix_nano": int(timestamp.timestamp() * 1e9),
                "end_time_unix_nano": int((timestamp + timedelta(milliseconds=50)).timestamp() * 1e9),
                "status": {"code": 0},
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "http.status_code", "value": {"intValue": 200}},
                ],
                "events": [],
                "links": [],
            }
        )

    return {
        "resource": {
            "attributes": [
                {"key": "service.name", "value": {"stringValue": service_name}},
                {"key": "service.namespace", "value": {"stringValue": namespace}},
            ]
        },
        "scopeSpans": [{"spans": spans}],
    }


class TestIngestionPerformance:
    """Benchmark ingestion performance."""

    def test_concurrent_trace_ingestion(self, postgres_storage):
        """Test concurrent trace ingestion throughput."""
        num_batches = 100
        spans_per_batch = 100
        num_workers = 10

        def ingest_batch(batch_id: int):
            """Ingest a batch of traces."""
            resource_spans = make_resource_spans(
                num_spans=spans_per_batch, service_name=f"service-{batch_id % 5}", namespace="benchmark"
            )
            postgres_storage.store_traces([resource_spans])

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(ingest_batch, i) for i in range(num_batches)]
            for future in as_completed(futures):
                future.result()  # Wait for completion

        elapsed = time.time() - start_time
        total_spans = num_batches * spans_per_batch
        throughput = total_spans / elapsed
        throughput_per_core = throughput / NUM_CORES

        print("\n=== Trace Ingestion Benchmark ===")
        print(f"Total spans: {total_spans}")
        print(f"Batches: {num_batches}")
        print(f"Spans per batch: {spans_per_batch}")
        print(f"Workers: {num_workers}")
        print(f"CPU cores: {NUM_CORES}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Throughput: {throughput:.0f} spans/sec ({throughput_per_core:.0f} spans/sec/core)")
        print(f"Latency per batch: {elapsed / num_batches * 1000:.2f}ms")

        # Assert reasonable performance (adjust based on hardware)
        assert throughput > 200, f"Expected >200 spans/sec, got {throughput:.0f}"
        assert elapsed < 60, f"Expected <60s total time, got {elapsed:.2f}s"

    def test_sequential_ingestion_baseline(self, postgres_storage):
        """Test sequential ingestion as baseline comparison."""
        num_batches = 20
        spans_per_batch = 50

        start_time = time.time()

        for i in range(num_batches):
            resource_spans = make_resource_spans(
                num_spans=spans_per_batch, service_name=f"service-{i % 3}", namespace="sequential"
            )
            postgres_storage.store_traces([resource_spans])

        elapsed = time.time() - start_time
        total_spans = num_batches * spans_per_batch
        throughput = total_spans / elapsed
        throughput_per_core = throughput / NUM_CORES

        print("\n=== Sequential Ingestion Baseline ===")
        print(f"Total spans: {total_spans}")
        print(f"Batches: {num_batches}")
        print(f"CPU cores: {NUM_CORES}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Throughput: {throughput:.0f} spans/sec ({throughput_per_core:.0f} spans/sec/core)")
        print(f"Latency per batch: {elapsed / num_batches * 1000:.2f}ms")

        assert throughput > 50, f"Expected >50 spans/sec, got {throughput:.0f}"

    def test_concurrent_log_ingestion(self, postgres_storage):
        """Test concurrent log ingestion throughput."""
        num_batches = 100
        logs_per_batch = 100
        num_workers = 10

        def make_resource_logs(num_logs: int, service_name: str, namespace: str = "benchmark") -> dict:
            """Generate OTLP ResourceLogs with test data."""
            now = datetime.now(UTC)
            log_records = []
            for i in range(num_logs):
                timestamp = now - timedelta(milliseconds=i * 10)
                log_records.append(
                    {
                        "time_unix_nano": int(timestamp.timestamp() * 1e9),
                        "observed_time_unix_nano": int(timestamp.timestamp() * 1e9),
                        "severity_number": 9,  # INFO
                        "severity_text": "INFO",
                        "body": {"stringValue": f"Log message {i}"},
                        "attributes": [
                            {"key": "log.level", "value": {"stringValue": "info"}},
                            {"key": "http.method", "value": {"stringValue": "GET"}},
                        ],
                        "trace_id": f"{i:032x}",
                        "span_id": f"{i:016x}",
                    }
                )

            return {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "service.namespace", "value": {"stringValue": namespace}},
                    ]
                },
                "scopeLogs": [{"log_records": log_records}],
            }

        def ingest_batch(batch_id: int):
            """Ingest a batch of logs."""
            resource_logs = make_resource_logs(
                num_logs=logs_per_batch, service_name=f"service-{batch_id % 5}", namespace="benchmark"
            )
            postgres_storage.store_logs([resource_logs])

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(ingest_batch, i) for i in range(num_batches)]
            for future in as_completed(futures):
                future.result()

        elapsed = time.time() - start_time
        total_logs = num_batches * logs_per_batch
        throughput = total_logs / elapsed
        throughput_per_core = throughput / NUM_CORES

        print("\n=== Log Ingestion Benchmark ===")
        print(f"Total log records: {total_logs}")
        print(f"Batches: {num_batches}")
        print(f"Records per batch: {logs_per_batch}")
        print(f"Workers: {num_workers}")
        print(f"CPU cores: {NUM_CORES}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Throughput: {throughput:.0f} logs/sec ({throughput_per_core:.0f} logs/sec/core)")
        print(f"Latency per batch: {elapsed / num_batches * 1000:.2f}ms")

        assert throughput > 200, f"Expected >200 logs/sec, got {throughput:.0f}"
        assert elapsed < 60, f"Expected <60s total time, got {elapsed:.2f}s"

    def test_concurrent_metric_ingestion(self, postgres_storage):
        """Test concurrent metric ingestion throughput."""
        num_batches = 100
        datapoints_per_batch = 100  # Data points, not metrics
        num_workers = 10

        def make_resource_metrics(num_datapoints: int, service_name: str, namespace: str = "benchmark") -> dict:
            """Generate OTLP ResourceMetrics with test data."""
            now = datetime.now(UTC)
            # Create metrics with multiple data points
            data_points = []
            for i in range(num_datapoints):
                timestamp = now - timedelta(milliseconds=i * 10)
                data_points.append(
                    {
                        "time_unix_nano": int(timestamp.timestamp() * 1e9),
                        "as_double": 50.0 + (i % 100),
                        "attributes": [
                            {"key": "http.method", "value": {"stringValue": "GET"}},
                            {"key": "http.status_code", "value": {"intValue": 200}},
                        ],
                    }
                )

            return {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}},
                        {"key": "service.namespace", "value": {"stringValue": namespace}},
                    ]
                },
                "scopeMetrics": [
                    {
                        "metrics": [
                            {
                                "name": "http.server.duration",
                                "unit": "ms",
                                "gauge": {"data_points": data_points},
                            }
                        ]
                    }
                ],
            }

        def ingest_batch(batch_id: int):
            """Ingest a batch of metrics."""
            resource_metrics = make_resource_metrics(
                num_datapoints=datapoints_per_batch, service_name=f"service-{batch_id % 5}", namespace="benchmark"
            )
            postgres_storage.store_metrics([resource_metrics])

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(ingest_batch, i) for i in range(num_batches)]
            for future in as_completed(futures):
                future.result()

        elapsed = time.time() - start_time
        total_datapoints = num_batches * datapoints_per_batch
        throughput = total_datapoints / elapsed
        throughput_per_core = throughput / NUM_CORES

        print("\n=== Metric Ingestion Benchmark ===")
        print(f"Total data points: {total_datapoints}")
        print(f"Batches: {num_batches}")
        print(f"Data points per batch: {datapoints_per_batch}")
        print(f"Workers: {num_workers}")
        print(f"CPU cores: {NUM_CORES}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Throughput: {throughput:.0f} datapoints/sec ({throughput_per_core:.0f} datapoints/sec/core)")
        print(f"Latency per batch: {elapsed / num_batches * 1000:.2f}ms")

        assert throughput > 200, f"Expected >200 datapoints/sec, got {throughput:.0f}"
        assert elapsed < 60, f"Expected <60s total time, got {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
