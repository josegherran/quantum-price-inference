# =============================================================================
# quantum-price-inference — Makefile
#
# All commands use `uv run` so the project venv is always used regardless of
# whether it is activated.  Run `make help` to see available targets.
#
# Prerequisites:
#   uv     https://docs.astral.sh/uv/
#   docker https://docs.docker.com/get-docker/
# =============================================================================

.DEFAULT_GOAL := help
.PHONY: help install install-dev install-notebook \
        lint format format-check typecheck test test-unit test-integration test-cov \
        api notebook \
        docker-build docker-run docker-stop docker-logs \
        deploy-up deploy-down deploy-logs deploy-ps \
        ci clean

COMPOSE_FILE := deploy/docker-compose.yml
IMAGE        := quantum-price-inference:latest

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

install: ## Install core dependencies only
	uv sync

install-dev: ## Install core + dev dependencies (pytest, ruff)
	uv sync --extra dev

install-notebook: ## Install all dependencies including notebook extras
	uv sync --extra dev --extra notebook

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter
	uv run ruff check .

format: ## Auto-format with ruff
	uv run ruff format .

format-check: ## Check formatting without modifying files (CI mode)
	uv run ruff format --check .

typecheck: ## Run mypy static type checker
	uv run mypy quantum_price_inference/ api/

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run full test suite
	uv run pytest --tb=short

test-unit: ## Run unit tests only (no qiskit-finance required)
	uv run pytest --tb=short -m "not integration"

test-integration: ## Run integration tests (requires --extra notebook)
	uv run pytest --tb=short -m integration

test-cov: ## Run tests with coverage report (Wave 3.2 — add pytest-cov first)
	@echo "Wave 3.2: uv run pytest --cov=quantum_price_inference --cov=api --cov-report=term-missing"
	@echo "          Add pytest-cov to dev deps first."

# ---------------------------------------------------------------------------
# Local development servers
# ---------------------------------------------------------------------------

api: ## Start the FastAPI development server with auto-reload
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

notebook: ## Launch Jupyter notebook (requires --extra notebook)
	uv run jupyter notebook notebook/quantum_price_inference.ipynb

# ---------------------------------------------------------------------------
# Docker — single container (API only)
# ---------------------------------------------------------------------------

docker-build: ## Build the API Docker image
	docker build -f deploy/Dockerfile -t $(IMAGE) .

docker-run: ## Run the API container locally on port 8000
	docker run --rm -p 8000:8000 --name qpi-api $(IMAGE)

docker-stop: ## Stop the running API container
	docker stop qpi-api

docker-logs: ## Tail logs from the running API container
	docker logs -f qpi-api

# ---------------------------------------------------------------------------
# Docker Compose — full stack (API + Prometheus + Grafana)
# ---------------------------------------------------------------------------

deploy-up: ## Start the full stack (detached)
	@[ -f deploy/.env ] || cp deploy/.env.example deploy/.env
	docker compose -f $(COMPOSE_FILE) up -d --build

deploy-down: ## Stop and remove the full stack
	docker compose -f $(COMPOSE_FILE) down

deploy-logs: ## Tail logs from all compose services
	docker compose -f $(COMPOSE_FILE) logs -f

deploy-ps: ## Show status of all compose services
	docker compose -f $(COMPOSE_FILE) ps

# ---------------------------------------------------------------------------
# CI — chains all quality checks (mirrors GitHub Actions)
# ---------------------------------------------------------------------------

ci: lint format-check typecheck test ## Run lint + format-check + typecheck + full test suite

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove build artefacts, caches, and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
