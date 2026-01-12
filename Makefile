.PHONY: help install dev test lint format typecheck ci clean docker-build docker-build-private docker-run up up-full down logs status setup-network

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
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

test-api: ## Run API tests with hurl (requires service running)
	@echo "$(CYAN)Running API tests with hurl...$(RESET)"
	@if ! command -v hurl >/dev/null 2>&1; then \
		echo "$(RED)❌ hurl not installed. Install: https://hurl.dev/docs/installation.html$(RESET)"; \
		exit 1; \
	fi
	@hurl --test --file-root . tests/api/**/*.hurl --variables-file tests/api/.env && \
		echo "$(GREEN)✅ All API tests passed$(RESET)" || \
		(echo "$(RED)❌ Some tests failed$(RESET)"; exit 1)

test-api-health: ## Run health check tests only
	@hurl --test --file-root . tests/api/health/*.hurl --variables-file tests/api/.env

test-api-scan: ## Run referral scan tests (requires ANTHROPIC_API_KEY)
	@hurl --test --file-root . tests/api/referral/referral_scan.hurl --variables-file tests/api/.env

test-api-match: ## Run test matching tests (requires test-catalog-service)
	@hurl --test --file-root . tests/api/referral/test_match.hurl --variables-file tests/api/.env

test-api-jwt: ## Run API tests with JWT authentication (requires auth service)
	@echo "$(YELLOW)🧪 Running API tests in JWT mode (with authentication)...$(RESET)"
	@if ! command -v hurl >/dev/null 2>&1; then \
		echo "$(RED)❌ hurl not installed. Install: https://hurl.dev/docs/installation.html$(RESET)"; \
		exit 1; \
	fi
	@echo "$(CYAN)ℹ️  Getting JWT access token from auth service...$(RESET)"
	@export access_token=$$(./scripts/get-jwt-token.sh) && \
		if [ -z "$$access_token" ]; then \
			echo "$(RED)❌ Failed to get access token$(RESET)"; \
			exit 1; \
		fi && \
		echo "$(GREEN)✅ Got access token$(RESET)" && \
		hurl --test --file-root . tests/api/**/*.hurl \
			--variables-file tests/api/.env \
			--variable access_token=$$access_token && \
		echo "$(GREEN)✅ All API tests passed (JWT mode)$(RESET)" || \
		(echo "$(RED)❌ Some tests failed$(RESET)"; exit 1)

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
	docker build -t pathlab-assist/pla-ai-referral-service:latest .

docker-build-private: ## Build Docker image (compatibility with start script, Python doesn't need GITHUB_TOKEN)
	docker build -t pathlab-assist/pla-ai-referral-service:latest .

docker-run: ## Run Docker container
	docker run --rm -p 8011:8080 --env-file .env pathlab-assist/pla-ai-referral-service:latest

# Docker Compose

setup-network: ## Create Docker network for PathLab services
	docker network create pathlab 2>/dev/null || true

up-full: setup-network ## Start service WITH LocalStack
	docker compose --profile full up -d
	@echo "$(GREEN)Service and LocalStack started$(RESET)"
	@echo "Service: http://localhost:8011"
	@echo "LocalStack: http://localhost:4566"

up: setup-network ## Start service only (requires existing LocalStack)
	docker compose up -d
	@echo "$(GREEN)Service started$(RESET)"
	@echo "Service: http://localhost:8011"

down: ## Stop service (keeps LocalStack running)
	docker compose down
	@echo "$(GREEN)Service stopped$(RESET)"

down-all: ## Stop everything including LocalStack
	docker compose --profile full down
	@echo "$(GREEN)All services stopped$(RESET)"

logs: ## View service logs
	docker compose logs -f ai-referral-service

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
