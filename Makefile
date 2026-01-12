.PHONY: help install dev test lint format typecheck ci clean docker-build docker-run up up-full down logs status setup-network

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN)Available targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# Development

install: ## Install dependencies
	pip install -e ".[dev]"

dev: ## Run development server with auto-reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 --app-dir src

# Testing

test: ## Run tests with coverage
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v

# Code Quality

lint: ## Run linter (ruff)
	ruff check src tests

format: ## Format code
	ruff format src tests

format-check: ## Check code formatting
	ruff format --check src tests

typecheck: ## Run type checker (mypy)
	mypy src

ci: lint typecheck test ## Run all CI checks

# Docker

docker-build: ## Build Docker image
	docker build -t pathlab-assist/pla-template-service:latest .

docker-run: ## Run Docker container
	docker run --rm -p 8080:8080 --env-file .env pathlab-assist/pla-template-service:latest

# Docker Compose

setup-network: ## Create Docker network for PathLab services
	docker network create pathlab 2>/dev/null || true

up-full: setup-network ## Start service WITH LocalStack
	docker compose --profile full up -d
	@echo "$(GREEN)Service and LocalStack started$(RESET)"
	@echo "Service: http://localhost:8080"
	@echo "LocalStack: http://localhost:4566"

up: setup-network ## Start service only (requires existing LocalStack)
	docker compose up -d
	@echo "$(GREEN)Service started$(RESET)"
	@echo "Service: http://localhost:8080"

down: ## Stop service (keeps LocalStack running)
	docker compose down
	@echo "$(GREEN)Service stopped$(RESET)"

down-all: ## Stop everything including LocalStack
	docker compose --profile full down
	@echo "$(GREEN)All services stopped$(RESET)"

logs: ## View service logs
	docker compose logs -f template-service

logs-localstack: ## View LocalStack logs
	docker compose logs -f localstack

status: ## Show service status
	@echo "$(CYAN)Service Status:$(RESET)"
	@docker compose ps
	@echo ""
	@echo "$(CYAN)LocalStack Status:$(RESET)"
	@docker ps --filter "name=pathlab-localstack" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Database

setup-db: ## Create DynamoDB tables in LocalStack
	./scripts/setup-db.sh

# Clean

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage
	@echo "$(GREEN)Cleaned generated files$(RESET)"
