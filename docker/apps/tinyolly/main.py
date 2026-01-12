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
TinyOlly - Unified Entry Point
Runs in either UI mode or OTLP Receiver mode based on MODE environment variable
"""

import os
import sys
import logging

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def start_ui_mode():
    """Start TinyOlly UI (FastAPI web application)"""
    # Configure OpenTelemetry for UI
    os.environ.setdefault('OTEL_SERVICE_NAME', 'tinyolly-ui')
    os.environ.setdefault('OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED', 'true')
    
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument()
    except ImportError:
        pass
    
    from app.main import app
    from app.config import settings
    import uvicorn
    
    port = settings.port
    logger.info("Starting TinyOlly UI...")
    logger.info(f"✓ HTTP mode: http://0.0.0.0:{port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


def start_receiver_mode():
    """Start OTLP Receiver (gRPC server)"""
    # Configure OpenTelemetry for receiver
    os.environ.setdefault('OTEL_SERVICE_NAME', 'tinyolly-otlp-receiver')
    os.environ.setdefault('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4318')
    os.environ.setdefault('OTEL_EXPORTER_OTLP_PROTOCOL', 'http/protobuf')
    os.environ.setdefault('OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED', 'true')
    
    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        LoggingInstrumentor().instrument()
    except ImportError:
        pass
    
    from receiver.server import start_receiver
    
    port = int(os.environ.get('PORT', 4343))
    start_receiver(port)


def main():
    """Main entry point - determine mode and start appropriate service"""
    mode = os.environ.get('MODE', 'ui').lower()
    
    if mode == 'ui':
        logger.info("Starting in UI mode")
        start_ui_mode()
    elif mode == 'receiver':
        logger.info("Starting in RECEIVER mode")
        start_receiver_mode()
    else:
        logger.error(f"Invalid MODE: {mode}. Must be 'ui' or 'receiver'")
        sys.exit(1)


if __name__ == '__main__':
    main()
