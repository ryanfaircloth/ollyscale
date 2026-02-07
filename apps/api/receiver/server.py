"""
ollyScale v2 OTLP Receiver - gRPC Server with PostgreSQL Storage

Receives OTLP data from OpenTelemetry Collector via gRPC and stores
directly in PostgreSQL database using the shared storage backend.
"""

import logging
import threading
import time
from concurrent import futures

import grpc
from google.protobuf.json_format import MessageToDict
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from opentelemetry.proto.collector.logs.v1 import logs_service_pb2, logs_service_pb2_grpc
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2, metrics_service_pb2_grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc

from app.dependencies import get_storage_sync
from app.storage.postgres_orm_sync import PostgresStorage

logger = logging.getLogger(__name__)

# Get storage backend instance
storage: PostgresStorage = None


def _convert_to_dict(proto_obj):
    """Convert protobuf message to dictionary recursively.

    Args:
        proto_obj: Protobuf message object

    Returns:
        Dictionary representation of the protobuf message
    """
    return MessageToDict(proto_obj, preserving_proto_field_name=True)


class TraceService(trace_service_pb2_grpc.TraceServiceServicer):
    """gRPC service for OTLP traces."""

    def Export(self, request, context):
        """Handle trace export requests."""
        try:
            # Convert protobuf to dict
            resource_spans = _convert_to_dict(request).get("resource_spans", [])

            if not resource_spans:
                logger.warning("Received empty trace request")
                return trace_service_pb2.ExportTraceServiceResponse()

            # Store traces using shared storage backend
            count = storage.store_traces(resource_spans)
            logger.info(f"Stored {count} spans from {len(resource_spans)} resource spans")

            return trace_service_pb2.ExportTraceServiceResponse()

        except Exception as e:
            logger.error(f"Failed to process traces: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process traces: {e!s}")
            return trace_service_pb2.ExportTraceServiceResponse()


class LogsService(logs_service_pb2_grpc.LogsServiceServicer):
    """gRPC service for OTLP logs."""

    def Export(self, request, context):
        """Handle log export requests."""
        try:
            # Convert protobuf to dict
            resource_logs = _convert_to_dict(request).get("resource_logs", [])

            if not resource_logs:
                logger.warning("Received empty log request")
                return logs_service_pb2.ExportLogsServiceResponse()

            # Store logs using shared storage backend
            count = storage.store_logs(resource_logs)
            logger.info(f"Stored {count} log records from {len(resource_logs)} resource logs")

            return logs_service_pb2.ExportLogsServiceResponse()

        except Exception as e:
            logger.error(f"Failed to process logs: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process logs: {e!s}")
            return logs_service_pb2.ExportLogsServiceResponse()


class MetricsService(metrics_service_pb2_grpc.MetricsServiceServicer):
    """gRPC service for OTLP metrics."""

    def Export(self, request, context):
        """Handle metric export requests."""
        try:
            # Convert protobuf to dict
            resource_metrics = _convert_to_dict(request).get("resource_metrics", [])

            if not resource_metrics:
                logger.warning("Received empty metrics request")
                return metrics_service_pb2.ExportMetricsServiceResponse()

            # Store metrics using shared storage backend
            count = storage.store_metrics(resource_metrics)
            logger.info(f"Stored {count} data points from {len(resource_metrics)} resource metrics")

            return metrics_service_pb2.ExportMetricsServiceResponse()

        except Exception as e:
            logger.error(f"Failed to process metrics: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to process metrics: {e!s}")
            return metrics_service_pb2.ExportMetricsServiceResponse()


def start_receiver(port: int = 4343):
    """Start the OTLP gRPC receiver server.

    Args:
        port: Port to listen on (default 4343)
    """
    global storage

    # Initialize storage backend
    storage = get_storage_sync()
    logger.info(f"Initialized PostgreSQL storage backend: {type(storage).__name__}")

    # Start background readiness checker (non-blocking)
    # This will check DB every 1s and connect when ready
    storage.start_readiness_checker()
    logger.info("Started database readiness checker")

    logger.info(f"Starting OTLP gRPC receiver on port {port}...")

    # Create sync gRPC server with ThreadPoolExecutor (20 workers for concurrent requests)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))

    # Register OTLP services
    trace_service_pb2_grpc.add_TraceServiceServicer_to_server(TraceService(), server)
    logs_service_pb2_grpc.add_LogsServiceServicer_to_server(LogsService(), server)
    metrics_service_pb2_grpc.add_MetricsServiceServicer_to_server(MetricsService(), server)

    # Register gRPC Health Checking Protocol
    # https://github.com/grpc/grpc/blob/master/doc/health-checking.md
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Set initial health status
    # "" (empty string) = overall server liveness (always SERVING once started)
    # "readiness" = readiness for traffic (NOT_SERVING until DB ready)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("readiness", health_pb2.HealthCheckResponse.NOT_SERVING)
    logger.info("Registered gRPC health checking services")

    # Start background thread to update readiness status
    def update_health_status():
        """Background thread to update health status based on storage readiness."""
        while True:
            try:
                # Check if ready and not in read-only mode
                if storage.is_ready and not storage.is_read_only_mode:
                    health_servicer.set("readiness", health_pb2.HealthCheckResponse.SERVING)
                else:
                    health_servicer.set("readiness", health_pb2.HealthCheckResponse.NOT_SERVING)
                    if storage.is_read_only_mode:
                        logger.warning("gRPC health: NOT_SERVING (read-only mode - migration in progress)")
            except Exception as e:
                logger.error(f"Error updating health status: {e}")
            time.sleep(1)  # Check every second

    health_thread = threading.Thread(target=update_health_status, daemon=True, name="health-status-updater")
    health_thread.start()

    # Bind to port and start server immediately
    # This allows liveness probe to pass while waiting for DB
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"✓ OTLP gRPC receiver listening on 0.0.0.0:{port}")
    logger.info("  (Waiting for database readiness before accepting data...)")

    try:
        server.wait_for_termination()
    finally:
        storage.close()
        logger.info("✓ Closed database connection")
