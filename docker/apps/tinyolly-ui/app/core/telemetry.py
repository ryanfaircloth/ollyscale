"""OpenTelemetry metrics setup"""

import os
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

from ..config import settings


def setup_telemetry():
    """Configure OpenTelemetry metrics"""
    # Set up OTLP metric exporter
    metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_exporter_otlp_metrics_endpoint
    )
    
    # Configure metric reader with 60s export interval
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    
    # Create meter for tinyolly-ui
    meter = metrics.get_meter("tinyolly-ui")
    
    # Create metrics
    request_counter = meter.create_counter(
        name="http.server.requests",
        description="Total HTTP requests",
        unit="1"
    )
    
    error_counter = meter.create_counter(
        name="http.server.errors",
        description="Total HTTP errors",
        unit="1"
    )
    
    response_time_histogram = meter.create_histogram(
        name="http.server.duration",
        description="HTTP request duration",
        unit="ms"
    )
    
    ingestion_counter = meter.create_counter(
        name="tinyolly.ingestion.count",
        description="Total telemetry ingestion operations",
        unit="1"
    )
    
    storage_operations_counter = meter.create_counter(
        name="tinyolly.storage.operations",
        description="Storage operations by type",
        unit="1"
    )
    
    return {
        "request_counter": request_counter,
        "error_counter": error_counter,
        "response_time_histogram": response_time_histogram,
        "ingestion_counter": ingestion_counter,
        "storage_operations_counter": storage_operations_counter,
    }


# Global metrics (initialized by setup_telemetry)
_metrics = None


def get_metrics():
    """Get the metrics dictionary"""
    global _metrics
    if _metrics is None:
        _metrics = setup_telemetry()
    return _metrics
