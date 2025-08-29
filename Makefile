.PHONY: help format format-check test test-cov lint clean install

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

format:  ## Format code with isort and black in correct order
	@echo "🎨 Formatting code..."
	python3 -m isort app/
	python3 -m black app/
	@echo "✅ Code formatting completed!"

format-check:  ## Check code formatting without making changes
	@echo "🔍 Checking code formatting..."
	python3 -m isort --check-only --diff app/
	python3 -m black --check --diff app/
	@echo "✅ Code formatting check passed!"

lint:  ## Run linting checks
	@echo "🔍 Running linting checks..."
	python3 -m flake8 app/ --max-line-length=120 --extend-ignore=E203,W503,E501,E722
	@echo "✅ Linting completed!"

test:  ## Run tests
	@echo "🧪 Running tests..."
	python3 -m pytest tests/ -v

test-py311:  ## Run tests with Python 3.11
	@echo "🧪 Running tests with Python 3.11..."
	python3.11 -m pytest tests/ -v

test-py312:  ## Run tests with Python 3.12
	@echo "🧪 Running tests with Python 3.12..."
	python3.12 -m pytest tests/ -v

test-cov:  ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	python3 -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

clean:  ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "✅ Cleanup completed!"

install:  ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip3 install -r requirements.txt
	pip3 install pre-commit
	pre-commit install
	@echo "✅ Installation completed!"

pre-commit:  ## Install pre-commit hooks
	@echo "🔧 Installing pre-commit hooks..."
	pip3 install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

ci-check: format-check lint test  ## Run all CI checks locally
	@echo "🎉 All CI checks passed locally!"
