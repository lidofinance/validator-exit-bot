FROM dhi.io/python:3.14.10-debian13-dev@sha256:331fffd6ff7fcf9bf5f7dbde8d48fad634375baa739d1db23f65e0ec83bcd198 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV POETRY_VERSION=1.8.2
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /build

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only main --no-root --no-directory

# Set by the CI build of the image; a build without these args keeps the placeholders of the repo file.
# The file is written here because the production image has no shell.
ARG BUILD_VERSION
ARG BUILD_BRANCH
ARG BUILD_COMMIT
COPY build-info.json ./
RUN if [ -n "$BUILD_COMMIT" ]; then \
      printf '{"version":"%s","branch":"%s","commit":"%s"}\n' \
        "$BUILD_VERSION" "$BUILD_BRANCH" "$BUILD_COMMIT" > build-info.json; \
    fi


FROM dhi.io/python:3.14.10-debian13@sha256:d20d953b545c83acd9e1b6b6b6d27cf14de38e6a39689334f71454c33cf41893 AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VENV_PATH="/.venv"

ENV PATH="$VENV_PATH/bin:$PATH"

# Copy only the virtual environment from builder
COPY --from=builder /build/.venv $VENV_PATH

WORKDIR /app

# Copy application code. 33 is www-data; the production image has no such name in /etc/passwd.
COPY --chown=33:33 src/ ./src/
COPY --chown=33:33 scripts/ ./scripts/
COPY --chown=33:33 interfaces/ ./interfaces/
COPY --from=builder --chown=33:33 /build/build-info.json ./

ENV PROMETHEUS_PORT=9000 \
    SERVER_PORT=9010

EXPOSE $PROMETHEUS_PORT $SERVER_PORT

# Switch to non-root user
USER 33:33

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python3", "-m", "src.healthcheck"]

ENTRYPOINT ["python3", "-m", "src.main"]
