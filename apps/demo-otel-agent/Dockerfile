# Multi-stage build using Poetry
FROM python:3.14-slim as builder

# Install Poetry
RUN pip install --no-cache-dir poetry>=1.8.0

# Configure Poetry: ensure venv is created in project and no dev deps by default
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/opt/poetry_cache

WORKDIR /app

# Copy Poetry configuration and source files
COPY pyproject.toml poetry.lock ./
COPY *.py ./

# Install dependencies into project venv
RUN poetry config virtualenvs.in-project true && poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.14-slim as runtime

# Copy virtual environment from builder stage
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app /app

WORKDIR /app

# Run directly - instrumentation is initialized in code
# agent.py is already in the venv from builder stage
# Works with both manual setup and OTel operator injection
CMD ["python", "-u", "agent.py"]
