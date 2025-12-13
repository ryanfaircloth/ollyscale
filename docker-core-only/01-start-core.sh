#!/bin/bash
set +e  # Don't exit on errors

echo "Starting TinyOlly Core (No OTel Collector)"
echo "=================================================="
echo ""
echo "Starting observability stack:"
echo "  - TinyOlly OTLP Receiver (listening on 4343)"
echo "  - TinyOlly OpAMP Server (listening on 4320/4321)"
echo "  - Redis"
echo "  - TinyOlly Frontend (web UI)"
echo ""
echo "NOTE: No OpenTelemetry Collector included."
echo "      Use your external collector (e.g., Elastic EDOT) and point it to:"
echo "      http://tinyolly-otlp-receiver:4343"
echo ""
echo "      Optional: Configure your external collector to connect to OpAMP server:"
echo "      ws://localhost:4320/v1/opamp (WebSocket endpoint)"
echo ""

echo "Starting services..."
echo ""

docker compose -f docker-compose-tinyolly-core.yml up -d --build --force-recreate 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "✗ Failed to start core services (exit code: $EXIT_CODE)"
    echo "Check the error messages above for details"
    exit 1
fi

echo ""
echo "Services started!"
echo ""

echo "TinyOlly UI:       http://localhost:5005"
echo "OTLP Endpoint:     localhost:4343 (gRPC only, for external collector)"
echo "OpAMP WebSocket:   ws://localhost:4320/v1/opamp (for external collector config management)"
echo ""
echo "Next steps:"
echo "  1. Configure your external collector to send telemetry to: localhost:4343 (gRPC)"
echo "     Note: TinyOlly receiver only supports gRPC. For HTTP, use a collector that"
echo "           accepts HTTP and forwards via gRPC."
echo "  2. (Optional) Configure your external collector to connect to OpAMP server:"
echo "     ws://localhost:4320/v1/opamp - this enables remote config management via TinyOlly UI"
echo "  3. Open TinyOlly UI: http://localhost:5005"
echo "  4. Stop services:    ./02-stop-core.sh"
echo ""

