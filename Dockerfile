# Optimized multi-stage Dockerfile
FROM python:3.12.4-slim as base

# Runtime dependencies only (removed build tools)
RUN apt-get update && apt-get install -y --no-install-recommends -qq \
    curl=7.88.1-10+deb12u14 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    VENV_PATH="/.venv"

ENV PATH="$VENV_PATH/bin:$PATH"


FROM base as builder

# Build dependencies installed only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends -qq \
    gcc=4:12.2.0-3 \
    libffi-dev=3.4.4-1 \
    g++=4:12.2.0-3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.2
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /build

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only main --no-root --no-directory


FROM base as production

# Copy only the virtual environment from builder
COPY --from=builder $VENV_PATH $VENV_PATH

WORKDIR /app

# Copy application code
COPY --chown=www-data:www-data src/ ./src/
COPY --chown=www-data:www-data interfaces/ ./interfaces/

ENV PROMETHEUS_PORT=9000 \
    SERVER_PORT=9010

EXPOSE $PROMETHEUS_PORT $SERVER_PORT

# Switch to non-root user
USER www-data

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$SERVER_PORT/health || exit 1

ENTRYPOINT ["python3", "src/main.py"]

