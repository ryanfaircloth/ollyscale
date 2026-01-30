"""
ollyScale v2 - Unified Entry Point
Runs in either frontend mode or OTLP receiver mode based on MODE environment variable.

For FRONTEND mode:
  - Production: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  - Development: python main.py (uses uvicorn for hot reload)

For RECEIVER mode:
  - python main.py (gRPC server with ThreadPoolExecutor)
"""

import contextlib
import logging
import os
import sys

from opentelemetry.instrumentation.logging import LoggingInstrumentor

from receiver.server import start_receiver

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def start_frontend_mode():
    """Start ollyScale v2 Frontend (FastAPI API server)

    NOTE: This uses uvicorn and is intended for DEVELOPMENT ONLY.
    For production, use Gunicorn:
      gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    """
    # Configure OpenTelemetry for frontend
    os.environ.setdefault("OTEL_SERVICE_NAME", "ollyscale-frontend")
    os.environ.setdefault("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true")

    with contextlib.suppress(ImportError):
        LoggingInstrumentor().instrument()

    port = int(os.environ.get("PORT", "8000"))
    logger.info("=" * 60)
    logger.info("Starting ollyScale v2 Frontend (DEVELOPMENT MODE)")
    logger.info("=" * 60)
    logger.info(f"✓ HTTP API: http://0.0.0.0:{port}")
    logger.info(f"✓ OpenAPI docs: http://0.0.0.0:{port}/docs")
    logger.info("")
    logger.info("For production, use Gunicorn:")
    logger.info("  gunicorn app.main:app --workers 4 \\")
    logger.info("    --worker-class uvicorn.workers.UvicornWorker \\")
    logger.info(f"    --bind 0.0.0.0:{port}")
    logger.info("=" * 60)

    # Import uvicorn conditionally (only needed in dev mode)
    try:
        import uvicorn  # noqa: PLC0415
    except ImportError:
        logger.error("uvicorn not installed. Install with: uv sync --all-groups")
        sys.exit(1)

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info", reload=True)


def start_receiver_mode():
    """Start OTLP Receiver (gRPC server writing to PostgreSQL)"""
    # Configure OpenTelemetry for receiver
    # NOTE: OTEL_PYTHON_DISABLED_INSTRUMENTATIONS must be set in deployment env vars
    # to take effect before auto-instrumentation initializes
    os.environ.setdefault("OTEL_SERVICE_NAME", "ollyscale-otlp-receiver")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    os.environ.setdefault("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true")

    with contextlib.suppress(ImportError):
        LoggingInstrumentor().instrument()

    port = int(os.environ.get("PORT", "4343"))
    logger.info("Starting ollyScale v2 OTLP Receiver...")
    logger.info(f"✓ gRPC endpoint: 0.0.0.0:{port}")
    logger.info("✓ Storage: PostgreSQL")

    start_receiver(port)


def main():
    """Main entry point - determine mode and start appropriate service"""
    mode = os.environ.get("MODE", "frontend").lower()

    if mode == "frontend":
        logger.info("Starting in FRONTEND mode")
        start_frontend_mode()
    elif mode == "receiver":
        logger.info("Starting in RECEIVER mode")
        start_receiver_mode()
    else:
        logger.error(f"Invalid MODE: {mode}. Must be 'frontend' or 'receiver'")
        sys.exit(1)


if __name__ == "__main__":
    main()
