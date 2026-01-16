# ollyScale Unified Dockerfile
# Single image that can run in either UI or RECEIVER mode
# Mode is selected via MODE environment variable

# Builder stage - install dependencies with Poetry
FROM python:3.14-slim AS builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry>=1.8.0

# Configure poetry: create virtual env in project for copying
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Create virtual environment and install dependencies
RUN python -m venv /app/venv && \
    . /app/venv/bin/activate && \
    poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Production stage - copy dependencies and application code
FROM python:3.14-slim AS production

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/venv /app/venv

# Add virtual environment to PATH
ENV PATH="/app/venv/bin:$PATH"

# Copy application code
COPY --chown=1000:1000 main.py .
COPY --chown=1000:1000 models.py .
COPY --chown=1000:1000 common/ common/
COPY --chown=1000:1000 app/ app/
COPY --chown=1000:1000 receiver/ receiver/

# Expose ports (both UI and receiver)
EXPOSE 5002
EXPOSE 4343

# Set Python to unbuffered mode for immediate log output
ENV PYTHONUNBUFFERED=1

# Run main.py which selects mode based on MODE env var
# MODE=ui (default) runs FastAPI UI on port 5002
# MODE=receiver runs gRPC receiver on port 4343
CMD ["python", "-u", "main.py"]
