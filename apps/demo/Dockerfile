# Unified demo image (frontend or backend) with Poetry multi-stage build

# Builder: install dependencies via Poetry into project venv
FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir poetry>=1.8.0
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy only dependency manifests for dependency install
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.in-project true && poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Runtime: copy the venv and app code; default CMD runs frontend
FROM python:3.13-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy both frontend and backend scripts
COPY frontend.py ./
COPY backend.py ./

EXPOSE 5000 8000

# Default to frontend, can be overridden at run-time
CMD ["python", "-u", "frontend.py"]
