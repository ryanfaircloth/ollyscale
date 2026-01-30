#!/bin/bash
# Production server startup script using Gunicorn
#
# Gunicorn with multiple workers provides:
# - Process-level parallelism (no GIL contention)
# - Better CPU utilization for sync workloads
# - Automatic worker restart on failure
# - Zero-downtime reloads

set -e

# Configuration
WORKERS=${WORKERS:-4}  # Number of worker processes (2-4 x CPU cores for I/O-bound)
PORT=${PORT:-8000}
BIND=${BIND:-0.0.0.0:$PORT}

# Worker sizing guidance:
# - I/O-bound workloads: 2-4 x CPU cores
# - CPU-bound workloads: 1 x CPU cores
# Default 4 workers works well for database-heavy operations

echo "Starting ollyscale-frontend with Gunicorn..."
echo "  Workers: $WORKERS"
echo "  Bind: $BIND"
echo "  Worker class: uvicorn.workers.UvicornWorker (ASGI with sync endpoints)"

exec uv run gunicorn app.main:app \
  --workers "$WORKERS" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "$BIND" \
  --log-level info \
  --access-logfile - \
  --error-logfile - \
  --timeout 120 \
  --graceful-timeout 30
