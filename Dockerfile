# Optimized multi-stage Dockerfile
FROM python:3.14.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    VENV_PATH="/.venv"

ENV PATH="$VENV_PATH/bin:$PATH"


FROM base AS builder

# Build dependencies installed only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends -qq \
    gcc=4:14.2.0-1 \
    libffi-dev=3.4.8-2 \
    g++=4:14.2.0-1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.2
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /build

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only main --no-root --no-directory


FROM base AS production

# Copy only the virtual environment from builder
COPY --from=builder /build/.venv $VENV_PATH

WORKDIR /app

# Copy application code
COPY --chown=www-data:www-data src/ ./src/
COPY --chown=www-data:www-data scripts/ ./scripts/
COPY --chown=www-data:www-data interfaces/ ./interfaces/

# Set by the CI build of the image; a build without these args keeps the placeholders of the repo file.
ARG BUILD_VERSION
ARG BUILD_BRANCH
ARG BUILD_COMMIT
COPY --chown=www-data:www-data build-info.json ./
# json.dump and not printf: a tag or a branch name may contain a quote.
RUN if [ -n "$BUILD_COMMIT" ]; then \
      python3 -c 'import json, sys; json.dump(dict(zip(("version", "branch", "commit"), sys.argv[1:])), open("build-info.json", "w"))' \
        "$BUILD_VERSION" "$BUILD_BRANCH" "$BUILD_COMMIT"; \
    fi

ENV PROMETHEUS_PORT=9000 \
    SERVER_PORT=9010

EXPOSE $PROMETHEUS_PORT $SERVER_PORT

# Switch to non-root user
USER www-data

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python3", "-m", "src.healthcheck"]

ENTRYPOINT ["python3", "-m", "src.main"]
