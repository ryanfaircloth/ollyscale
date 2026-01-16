# ollyScale - Observability Platform for Local Development
# Copyright (c) 2026 Ryan Faircloth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Based on ollyScale (BSD-3-Clause), see LICENSE-BSD3-ORIGINAL
# Original: https://github.com/ollyscale/ollyscale

"""
OllyScale - Unified Entry Point
Runs in either UI mode or OTLP Receiver mode based on MODE environment variable
"""

import logging
import os
import sys

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def start_ui_mode():
    """Start ollyScale UI (FastAPI web application)"""
    # Configure OpenTelemetry for UI
    os.environ.setdefault("OTEL_SERVICE_NAME", "ollyscale-ui")
    os.environ.setdefault("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true")

    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        LoggingInstrumentor().instrument()
    except ImportError:
        pass

    import uvicorn

    from app.config import settings
    from app.main import app

    port = settings.port
    logger.info("Starting ollyScale UI...")
    logger.info(f"✓ HTTP mode: http://0.0.0.0:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


def start_receiver_mode():
    """Start OTLP Receiver (gRPC server)"""
    # Configure OpenTelemetry for receiver
    os.environ.setdefault("OTEL_SERVICE_NAME", "ollyscale-otlp-receiver")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    os.environ.setdefault("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true")

    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        LoggingInstrumentor().instrument()
    except ImportError:
        pass

    from receiver.server import start_receiver

    port = int(os.environ.get("PORT", 4343))
    start_receiver(port)


def main():
    """Main entry point - determine mode and start appropriate service"""
    mode = os.environ.get("MODE", "ui").lower()

    if mode == "ui":
        logger.info("Starting in UI mode")
        start_ui_mode()
    elif mode == "receiver":
        logger.info("Starting in RECEIVER mode")
        start_receiver_mode()
    else:
        logger.error(f"Invalid MODE: {mode}. Must be 'ui' or 'receiver'")
        sys.exit(1)


if __name__ == "__main__":
    main()
