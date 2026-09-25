.PHONY: install install-dev test test-cov lint clean help run

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install MLX-Man in the active environment
	pip install -e .

install-dev: ## Install MLX-Man with development dependencies
	pip install -e ".[dev]"

test: ## Run the test suite
	pytest -v

test-cov: ## Run tests with coverage report
	pytest --cov=mlx_man --cov-report=term-missing -v

lint: ## Run linter (requires ruff)
	ruff check src/ tests/

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

run: ## Launch MLX-Man
	mlx-man
