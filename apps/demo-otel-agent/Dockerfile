# Multi-stage build using Poetry
FROM python:3.14-slim as builder

# Install Poetry
RUN pip install --no-cache-dir poetry>=1.8.0

# Configure Poetry: no virtual env (we're in container), no dev deps by default
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/opt/poetry_cache

WORKDIR /app

# Copy Poetry configuration
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.14-slim as runtime

# Copy virtual environment from builder stage
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app

# Copy application code
COPY agent.py ./

# Run directly - instrumentation is initialized in code
# Works with both manual setup and OTel operator injection
CMD ["python", "-u", "agent.py"]
