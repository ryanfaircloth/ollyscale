# Unified demo image (frontend or backend) with uv multi-stage build

# Builder: install dependencies via uv into project venv
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv - modern, fast Python package manager (10-100x faster than Poetry)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml uv.lock* ./
COPY frontend.py backend.py ./

# Install dependencies using uv (creates .venv in project)
RUN uv sync --frozen --no-dev

# Runtime: copy the venv and app code; default CMD runs frontend
FROM python:3.14-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy application scripts
COPY --from=builder /app/frontend.py /app/backend.py ./

EXPOSE 5000 8000

# Default to frontend, can be overridden at run-time
CMD ["python", "-u", "frontend.py"]
