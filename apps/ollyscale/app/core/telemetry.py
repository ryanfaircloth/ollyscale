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

"""OpenTelemetry telemetry setup

Note: When running in Kubernetes with the OpenTelemetry Operator,
auto-instrumentation is injected automatically via the Instrumentation CR.

Auto-instrumented components (no manual setup needed):
- FastAPI HTTP requests/responses (opentelemetry-instrumentation-fastapi)
- Redis operations (opentelemetry-instrumentation-redis)
- Logging with trace context (opentelemetry-instrumentation-logging)

This module only provides domain-specific metrics for OllyScale operations.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Global flag to track if telemetry is enabled
_telemetry_enabled = True


def _is_auto_instrumented() -> bool:
    """Check if the app is already auto-instrumented by the OTel Operator"""
    # The operator sets this env var when injecting instrumentation
    return os.getenv("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED") == "true"


def _is_telemetry_disabled() -> bool:
    """Check if telemetry should be disabled"""
    # Disable telemetry if OTEL_SDK_DISABLED is set
    return os.getenv("OTEL_SDK_DISABLED", "false").lower() in ("true", "1", "yes")


def setup_telemetry():
    """Configure domain-specific OpenTelemetry metrics

    When running in Kubernetes with OTel Operator, the operator automatically:
    - Injects the opentelemetry-instrument wrapper
    - Sets all OTEL_* environment variables
    - Configures exporters to send to the collector
    - Instruments FastAPI, Redis, and logging automatically

    This function only defines OllyScale-specific business metrics.
    """
    global _telemetry_enabled  # noqa: PLW0603

    # Check if telemetry is explicitly disabled
    if _is_telemetry_disabled():
        logger.info("OpenTelemetry SDK is disabled via OTEL_SDK_DISABLED environment variable")
        _telemetry_enabled = False
        return _create_noop_metrics()

    # Check if auto-instrumented by operator
    if _is_auto_instrumented():
        logger.info("Auto-instrumentation detected - using operator-injected configuration")
    else:
        logger.info("Running without auto-instrumentation (development mode)")

    try:
        from opentelemetry import metrics  # noqa: PLC0415

        # Get the meter - operator will have already configured the provider
        meter = metrics.get_meter("ollyscale-ui")

        # Domain-specific metrics for ollyScale ingestion operations
        # These are business metrics, not infrastructure metrics
        ingestion_counter = meter.create_counter(
            name="ollyscale.ingestion.count",
            description="Total telemetry items ingested by type (spans, logs, metrics)",
            unit="1",
        )

        storage_operations_counter = meter.create_counter(
            name="ollyscale.storage.operations",
            description="Storage operations by type (store_spans, store_logs, store_metrics)",
            unit="1",
        )

        logger.info("OpenTelemetry domain-specific metrics initialized successfully")
        return {
            "ingestion_counter": ingestion_counter,
            "storage_operations_counter": storage_operations_counter,
        }

    except Exception as e:
        # If telemetry setup fails, log and continue with noop metrics
        logger.warning(
            f"Failed to initialize OpenTelemetry metrics: {e}. Application will continue without custom metrics."
        )
        _telemetry_enabled = False
        return _create_noop_metrics()


def _create_noop_metrics():
    """Create no-op metrics that do nothing when called"""

    class NoopMetric:
        def add(self, *args, **kwargs):
            pass

        def record(self, *args, **kwargs):
            pass

    noop = NoopMetric()
    return {
        "ingestion_counter": noop,
        "storage_operations_counter": noop,
    }


# Global metrics (initialized by setup_telemetry)
_metrics = None


def get_metrics():
    """Get the metrics dictionary"""
    global _metrics  # noqa: PLW0603
    if _metrics is None:
        _metrics = setup_telemetry()
    return _metrics
