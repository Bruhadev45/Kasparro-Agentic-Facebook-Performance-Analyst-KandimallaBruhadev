.PHONY: help setup run test test-unit test-integration test-coverage lint format format-check type-check security clean ci install-hooks

help:
	@echo "Kasparro Agentic FB Analyst - Makefile Commands"
	@echo "================================================"
	@echo "Setup & Installation:"
	@echo "  make setup          - Create venv and install dependencies"
	@echo "  make install-hooks  - Install pre-commit hooks"
	@echo ""
	@echo "Running the System:"
	@echo "  make run QUERY='...'- Run analysis with query"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage  - Generate HTML coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black and isort"
	@echo "  make format-check   - Check code formatting"
	@echo "  make type-check     - Run type checking with mypy"
	@echo "  make security       - Run security checks"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci             - Run all CI checks locally"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Clean generated files"
	@echo "  make sample-data    - Create sample data file"

setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "Setup complete! Activate with: source .venv/bin/activate"

install-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed!"

run:
ifndef QUERY
	@echo "Usage: make run QUERY='Analyze ROAS drop in last 7 days'"
	@exit 1
endif
	python run.py "$(QUERY)"

# Testing targets
test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/ -v -m "not integration" --cov=src --cov-report=term-missing

test-integration:
	pytest tests/ -v -m integration --cov=src --cov-report=term-missing

test-coverage:
	pytest tests/ --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@which open > /dev/null && open htmlcov/index.html || echo "Open htmlcov/index.html in your browser"

# Code quality targets
lint:
	@echo "Running flake8..."
	flake8 src tests --max-line-length=88 --extend-ignore=E203,W503
	@echo "✓ Flake8 passed"

format:
	@echo "Formatting code with black..."
	black src tests
	@echo "Sorting imports with isort..."
	isort src tests --profile black
	@echo "✓ Code formatted"

format-check:
	@echo "Checking code formatting..."
	black src tests --check
	isort src tests --check --profile black
	@echo "✓ Format check passed"

type-check:
	@echo "Running type checking with mypy..."
	mypy src --ignore-missing-imports || echo "⚠ Type check warnings (non-blocking)"

security:
	@echo "Running security checks..."
	bandit -r src -ll || echo "⚠ Security warnings found"
	safety check || echo "⚠ Dependency vulnerabilities found"

# CI simulation
ci: format-check lint type-check test
	@echo "✓ All CI checks passed!"

# Cleanup
clean:
	@echo "Cleaning generated files..."
	rm -rf reports/*.md reports/*.json logs/*.json
	rm -rf .pytest_cache __pycache__ **/__pycache__ **/*.pyc
	rm -rf .coverage htmlcov/
	rm -rf .mypy_cache
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"

sample-data:
	head -100 data/synthetic_fb_ads_undergarments.csv > data/sample_fb_ads.csv
	@echo "Sample data created: data/sample_fb_ads.csv"
