.PHONY: help build up down restart logs shell health metrics clean rebuild test test-cov test-watch

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
	@echo "  test        Run unit tests"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  test-watch  Run tests in watch mode"
	@echo "  run         Run bot locally (loads .env)"
	@echo "  run-dry     Run bot locally in dry-run mode"

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
		export $$(cat .env | grep -v '^#' | xargs) && poetry run python src/main.py; \
	else \
		echo "❌ .env file not found"; \
		exit 1; \
	fi

# Run bot locally in dry-run mode
run-dry:
	@echo "Running bot in dry-run mode..."
	@if [ -f .env ]; then \
		echo "✅ Loading .env file with DRY_RUN=true"; \
		export $$(cat .env | grep -v '^#' | xargs) && export DRY_RUN=true && poetry run python src/main.py; \
	else \
		echo "❌ .env file not found"; \
		exit 1; \
	fi

