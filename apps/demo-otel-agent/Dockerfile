# Multi-stage build using uv (10-100x faster than Poetry)
FROM python:3.14-slim as builder

WORKDIR /app

# Install uv - modern, fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml uv.lock* ./
COPY *.py ./

# Install dependencies using uv (creates .venv in project)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Production stage
FROM python:3.14-slim as runtime

# Copy virtual environment and application from builder stage
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app /app

WORKDIR /app

# Run directly - instrumentation is initialized in code
# Works with both manual setup and OTel operator injection
CMD ["python", "-u", "agent.py"]
