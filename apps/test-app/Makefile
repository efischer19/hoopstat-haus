.PHONY: help install dev-setup test lint format security clean docker-build docker-run

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev-setup: install ## Set up development environment
	poetry run pre-commit install
	@echo "✅ Development environment set up successfully"
	@echo "📝 Run 'make test' to verify everything works"

test: ## Run tests with coverage
	poetry run test

lint: ## Run linting
	poetry run lint

format: ## Format code
	poetry run format

format-check: ## Check code formatting
	poetry run format-check

security: ## Run security scans
	poetry run security-deps || true
	poetry run security-code || true

pre-commit: ## Run pre-commit checks (format, lint, test)
	poetry run format-check
	poetry run lint
	poetry run test

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

docker-build: ## Build Docker image
	docker build -t test-app:latest .

docker-run: docker-build ## Build and run Docker container
	docker run --rm -it test-app:latest

# Development workflow targets
dev: dev-setup test ## Quick development setup and test

ci: format-check lint test security ## Run all CI checks locally

# Show current status
status: ## Show git and poetry status
	@echo "=== Git Status ==="
	git status --short
	@echo ""
	@echo "=== Poetry Status ==="
	poetry show --tree