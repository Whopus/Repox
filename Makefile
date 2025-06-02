# Makefile for Repox development

.PHONY: help install install-dev test test-cov lint format type-check clean build upload demo

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=repox --cov-report=html --cov-report=term

lint:  ## Run linting
	flake8 src/repox tests examples
	isort --check-only src/repox tests examples
	black --check src/repox tests examples

format:  ## Format code
	isort src/repox tests examples
	black src/repox tests examples

type-check:  ## Run type checking
	mypy src/repox

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build the package
	python -m build

upload:  ## Upload to PyPI (requires authentication)
	python -m twine upload dist/*

demo:  ## Run the interactive demo
	cd examples && python demo.py

# Development workflow targets
dev-setup: install-dev  ## Set up development environment
	@echo "Development environment set up!"
	@echo "Don't forget to set your environment variables:"
	@echo "  export OPENAI_API_KEY='your-api-key'"
	@echo "  export REPOX_STRONG_MODEL='gpt-4'"
	@echo "  export REPOX_WEAK_MODEL='gpt-3.5-turbo'"

check: lint type-check test  ## Run all checks

release: clean check build  ## Prepare a release
	@echo "Release ready! Run 'make upload' to publish to PyPI."