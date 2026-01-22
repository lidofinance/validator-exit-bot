.PHONY: help build up down restart logs shell health metrics clean rebuild test test-cov test-watch lint format generate-et-hash generate-veb-data

# Default target
help:
	@echo "Validator Exit Bot - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build       Build the Docker image"
	@echo "  up          Start the bot in detached mode"
	@echo "  down        Stop and remove the bot container"
	@echo "  restart     Restart the bot"
	@echo "  logs        Follow the bot logs"
	@echo "  shell       Open a shell in the running container"
	@echo "  health      Check the bot health status"
	@echo "  metrics     Display Prometheus metrics"
	@echo "  clean       Remove containers, images, and volumes"
	@echo "  rebuild     Clean rebuild (no cache)"
	@echo "  config      Validate and view docker-compose config"
	@echo "  ps          Show running containers"
	@echo "  install     Install all dependencies"
	@echo "  test        Run unit tests"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  test-watch  Run tests in watch mode"
	@echo "  lint        Run linter (ruff check)"
	@echo "  format      Format code (ruff format + fix imports)"
	@echo "  run         Run bot locally (loads .env)"
	@echo "  run-dry     Run bot locally in dry-run mode"
	@echo ""
	@echo "Script Generation (Docker):"
	@echo "  generate-et-hash    Generate Easy Track hash calldata via Docker"
	@echo "  generate-veb-data   Generate VEB data calldata via Docker"

# Build the Docker image
build:
	docker-compose build

# Start services in detached mode
up:
	docker-compose up -d
	@echo "Bot started. Check logs with: make logs"
	@echo "Check health with: make health"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart
	@echo "Bot restarted. Check logs with: make logs"

# Follow logs
logs:
	docker-compose logs -f validator-exit-bot

# Open shell in container
shell:
	docker-compose exec validator-exit-bot /bin/bash

# Check health
health:
	@echo "Checking bot health..."
	@SERVER_PORT=$${SERVER_PORT:-9010}; \
	curl -f http://localhost:$$SERVER_PORT/health || echo "❌ Health check failed"
	@echo ""

# Display metrics
metrics:
	@echo "Fetching Prometheus metrics..."
	@PROMETHEUS_PORT=$${PROMETHEUS_PORT:-9000}; \
	curl -s http://localhost:$$PROMETHEUS_PORT/metrics | grep -v "^#" | head -20
	@echo ""
	@PROMETHEUS_PORT=$${PROMETHEUS_PORT:-9000}; \
	echo "Full metrics available at: http://localhost:$$PROMETHEUS_PORT/metrics"

# Clean up everything
clean:
	docker-compose down -v
	docker rmi lidofinance/validator-exit-bot:latest || true
	@echo "Cleaned up containers, volumes, and images"

# Rebuild from scratch
rebuild:
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Rebuilt and restarted"

# Validate configuration
config:
	docker-compose config

# Show running containers
ps:
	docker-compose ps

# Setup environment (copy example if .env doesn't exist)
setup:
	@if [ ! -f .env ]; then \
		echo "Creating .env from env.example..."; \
		cp env.example .env; \
		echo "⚠️  Please edit .env with your configuration"; \
	else \
		echo ".env already exists"; \
	fi

# Development mode with live logs
dev:
	docker-compose up

# Check Docker and docker-compose installation
check:
	@echo "Checking requirements..."
	@docker --version || echo "❌ Docker not found"
	@docker-compose --version || echo "❌ docker-compose not found"
	@echo "✅ All requirements met"

install:
	@echo "Install dependencies using poetry for developing"
	@echo ""
	poetry install --with dev

# Lint code with ruff
lint:
	@echo "Running ruff linter..."
	poetry run ruff check src/ tests/ scripts/

# Format code with ruff
format:
	@echo "Formatting code with ruff..."
	poetry run ruff check src/ tests/ scripts/ --fix
	poetry run ruff format src/ tests/ scripts/
	@echo "✅ Code formatted"

# Run unit tests
test:
	@echo "Running unit tests..."
	poetry run pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	poetry run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Run tests in watch mode (requires pytest-watch)
test-watch:
	@echo "Running tests in watch mode..."
	poetry run ptw tests/

# Run bot locally (with .env loaded)
run:
	@echo "Running bot locally with .env..."
	@if [ -f .env ]; then \
		echo "✅ Loading .env file"; \
		export $$(cat .env | grep -v '^#' | xargs) && poetry run python -m src.main; \
	else \
		echo "❌ .env file not found"; \
		exit 1; \
	fi

# Run bot locally in dry-run mode
run-dry:
	@echo "Running bot in dry-run mode..."
	@if [ -f .env ]; then \
		echo "✅ Loading .env file with DRY_RUN=true"; \
		export $$(cat .env | grep -v '^#' | xargs) && export DRY_RUN=true && poetry run python -m src.main; \
	else \
		echo "❌ .env file not found"; \
		exit 1; \
	fi

# Generate Easy Track hash calldata via Docker
# Usage: make generate-et-hash VI=123456 [VI2=123457] [KAPI_URL=...] [CL_URL=...]
generate-et-hash:
	@if [ -z "$(VI)" ]; then \
		echo "❌ Error: VI (validator index) is required"; \
		echo "Usage: make generate-et-hash VI=123456"; \
		echo "       make generate-et-hash VI=123456 VI2=123457 VI3=123458"; \
		exit 1; \
	fi
	@echo "🔨 Building Docker image..."
	@docker build -t validator-exit-bot . -q
	@echo "📊 Generating Easy Track hash calldata..."
	@KAPI_URL=$${KAPI_URL:-https://keys-api.lido.fi}; \
	CL_URL=$${CL_URL:-http://host.docker.internal:5052}; \
	VI_ARGS="--vi $(VI)"; \
	if [ ! -z "$(VI2)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI2)"; fi; \
	if [ ! -z "$(VI3)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI3)"; fi; \
	if [ ! -z "$(VI4)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI4)"; fi; \
	if [ ! -z "$(VI5)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI5)"; fi; \
	docker run --rm validator-exit-bot \
		python3 -m scripts.generate \
		--kapi-url $$KAPI_URL \
		--cl-url $$CL_URL \
		et-hash \
		$$VI_ARGS

# Generate VEB data calldata via Docker
# Usage: make generate-veb-data VI=123456 [VI2=123457] [KAPI_URL=...] [CL_URL=...]
generate-veb-data:
	@if [ -z "$(VI)" ]; then \
		echo "❌ Error: VI (validator index) is required"; \
		echo "Usage: make generate-veb-data VI=123456"; \
		echo "       make generate-veb-data VI=123456 VI2=123457 VI3=123458"; \
		exit 1; \
	fi
	@echo "🔨 Building Docker image..."
	@docker build -t validator-exit-bot . -q
	@echo "📊 Generating VEB data calldata..."
	@KAPI_URL=$${KAPI_URL:-https://keys-api.lido.fi}; \
	CL_URL=$${CL_URL:-http://host.docker.internal:5052}; \
	VI_ARGS="--vi $(VI)"; \
	if [ ! -z "$(VI2)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI2)"; fi; \
	if [ ! -z "$(VI3)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI3)"; fi; \
	if [ ! -z "$(VI4)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI4)"; fi; \
	if [ ! -z "$(VI5)" ]; then VI_ARGS="$$VI_ARGS --vi $(VI5)"; fi; \
	docker run --rm validator-exit-bot \
		python3 -m scripts.generate \
		--kapi-url $$KAPI_URL \
		--cl-url $$CL_URL \
		veb-data \
		$$VI_ARGS
