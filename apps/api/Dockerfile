# ollyScale v2 Frontend - PostgreSQL-backed API with Gunicorn
# Python 3.14 FastAPI application with sync storage and multi-process workers

# Builder stage - install dependencies with uv (10-100x faster than Poetry)
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv - modern, fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy only dependency files first (enables layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv (creates .venv in project)
# This layer is cached unless pyproject.toml or uv.lock changes
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy source code after dependencies are installed
# Code changes won't invalidate the dependency layer
COPY app/ app/
COPY common/ common/
COPY receiver/ receiver/
COPY main.py .

# Production stage - copy dependencies and application code
FROM python:3.14-slim AS production

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code, receiver, and migrations
COPY --chown=1000:1000 app/ app/
COPY --chown=1000:1000 common/ common/
COPY --chown=1000:1000 receiver/ receiver/
COPY --chown=1000:1000 alembic/ alembic/
COPY --chown=1000:1000 alembic.ini .
COPY --chown=1000:1000 main.py .

# Create non-root user
RUN useradd -u 1000 -m ollyscale && \
    chown -R 1000:1000 /app

# Switch to non-root user
USER 1000

# Expose API port
EXPOSE 8000

# Set Python to unbuffered mode for immediate log output
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Default command: run with Gunicorn for production (4 workers, multi-process)
# For receiver mode: set MODE=receiver to use gRPC server instead
CMD ["sh", "-c", "if [ \"$MODE\" = 'receiver' ]; then python main.py; else exec gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --log-level info --access-logfile - --error-logfile -; fi"]
