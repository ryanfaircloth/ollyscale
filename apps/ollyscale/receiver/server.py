# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
ollyScale OTLP Receiver - gRPC Implementation with Async Storage
Receives OTLP data from OpenTelemetry Collector via gRPC and stores in Redis
Optimized with Batch Operations and uvloop
"""

import asyncio
import logging
import threading
import time
from concurrent import futures

import grpc
import uvloop
from opentelemetry.proto.collector.logs.v1 import logs_service_pb2, logs_service_pb2_grpc
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2, metrics_service_pb2_grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc

from common import Storage

# Configure logging
logger = logging.getLogger(__name__)

storage = Storage()

# Create a dedicated event loop for async operations
_loop = None
_loop_thread = None


def get_event_loop():
    """Get or create the shared event loop running in a background thread"""
    global _loop, _loop_thread

    if _loop is None:

        def run_loop():
            global _loop
            # Enable uvloop for performance
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            _loop.run_forever()

        _loop_thread = threading.Thread(target=run_loop, daemon=True)
        _loop_thread.start()

        # Wait for loop to be created
        while _loop is None:
            time.sleep(0.01)

    return _loop


def run_async(coro):
    """Run a coroutine in the shared event loop"""
    loop = get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


class TraceService(trace_service_pb2_grpc.TraceServiceServicer):
    """gRPC service for receiving traces"""

    def Export(self, request, context):
        """Handle trace export requests"""
        try:
            run_async(self._process_traces(request))
            return trace_service_pb2.ExportTraceServiceResponse()
        except Exception as e:
            logger.error(f"Error processing traces: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trace_service_pb2.ExportTraceServiceResponse()

    async def _process_traces(self, request):
        """Process traces asynchronously - convert protobuf to OTLP JSON"""
        from google.protobuf.json_format import MessageToDict

        otlp_data = MessageToDict(
            request,
            preserving_proto_field_name=False,
            always_print_fields_with_no_presence=False,
            use_integers_for_enums=False,
        )

        await storage.store_traces(otlp_data)


class LogsService(logs_service_pb2_grpc.LogsServiceServicer):
    """gRPC service for receiving logs"""

    def Export(self, request, context):
        """Handle log export requests"""
        try:
            run_async(self._process_logs(request))
            return logs_service_pb2.ExportLogsServiceResponse()
        except Exception as e:
            logger.error(f"Error processing logs: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return logs_service_pb2.ExportLogsServiceResponse()

    async def _process_logs(self, request):
        """Process logs asynchronously - convert protobuf to OTLP JSON"""
        from google.protobuf.json_format import MessageToDict

        otlp_data = MessageToDict(
            request,
            preserving_proto_field_name=False,
            always_print_fields_with_no_presence=False,
            use_integers_for_enums=False,
        )

        await storage.store_logs_otlp(otlp_data)


class MetricsService(metrics_service_pb2_grpc.MetricsServiceServicer):
    """gRPC service for receiving metrics"""

    def Export(self, request, context):
        """Handle metric export requests"""
        try:
            run_async(self._process_metrics(request))
            return metrics_service_pb2.ExportMetricsServiceResponse()
        except Exception as e:
            logger.error(f"Error processing metrics: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return metrics_service_pb2.ExportMetricsServiceResponse()

    async def _process_metrics(self, request):
        """Process metrics asynchronously - convert protobuf to OTLP JSON"""
        from google.protobuf.json_format import MessageToDict

        otlp_data = MessageToDict(
            request,
            preserving_proto_field_name=False,
            always_print_fields_with_no_presence=False,
            use_integers_for_enums=False,
        )

        await storage.store_metrics(otlp_data)


def start_receiver(port=4343):
    """Start the gRPC receiver server"""
    # Initialize the event loop before starting the server
    get_event_loop()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register services
    trace_service_pb2_grpc.add_TraceServiceServicer_to_server(TraceService(), server)
    logs_service_pb2_grpc.add_LogsServiceServicer_to_server(LogsService(), server)
    metrics_service_pb2_grpc.add_MetricsServiceServicer_to_server(MetricsService(), server)

    server.add_insecure_port(f"0.0.0.0:{port}")

    logger.info(f"ollyScale OTLP Receiver (gRPC) starting on port {port}...")

    # Check Redis connection
    redis_connected = run_async(storage.is_connected())
    logger.info(f"Redis connection: {redis_connected}")

    server.start()
    logger.info("✓ Server started successfully")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        server.stop(0)
