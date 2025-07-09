# OpenDict Makefile
# Development and build automation

.PHONY: help setup install test lint format type-check security-check clean build run docs dist package

# Default target
help:
	@echo "OpenDict Development Commands"
	@echo "============================"
	@echo "setup          - Set up development environment"
	@echo "install        - Install dependencies"
	@echo "test           - Run all tests"
	@echo "test-unit      - Run unit tests only"
	@echo "test-integration - Run integration tests only"
	@echo "test-coverage  - Run tests with coverage report"
	@echo "lint           - Run linting checks"
	@echo "format         - Format code"
	@echo "type-check     - Run type checking"
	@echo "security-check - Run security checks"
	@echo "quality-check  - Run all quality checks"
	@echo "clean          - Clean build artifacts"
	@echo "build          - Build Swift application"
	@echo "run-server     - Run Python transcription server"
	@echo "run-app        - Run Swift application"
	@echo "docs           - Generate documentation"
	@echo "pre-commit     - Install pre-commit hooks"
	@echo "dist           - Build distribution packages"
	@echo "dist-dev       - Build development distribution"
	@echo "dist-release   - Build release distribution"
	@echo "package        - Create installation packages"
	@echo "clean-dist     - Clean distribution artifacts"

# Environment setup
setup:
	@echo "Setting up development environment..."
	python3 setup.py

install:
	@echo "Installing Python dependencies..."
	venv/bin/pip install -r requirements-dev.txt

# Testing
test:
	@echo "Running all tests..."
	venv/bin/python -m pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	venv/bin/python -m pytest tests/ -v -m "unit"

test-integration:
	@echo "Running integration tests..."
	venv/bin/python -m pytest tests/ -v -m "integration"

test-coverage:
	@echo "Running tests with coverage..."
	venv/bin/python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "Running linting checks..."
	venv/bin/python -m flake8 .
	@echo "Linting completed."

format:
	@echo "Formatting Python code..."
	venv/bin/python -m black .
	venv/bin/python -m isort .
	@echo "Formatting Swift code..."
	-swiftformat OpenDictApp/
	@echo "Formatting completed."

type-check:
	@echo "Running type checking..."
	venv/bin/python -m mypy .
	@echo "Type checking completed."

security-check:
	@echo "Running security checks..."
	venv/bin/python -m bandit -r . -x tests/
	@echo "Security checking completed."

quality-check: lint type-check security-check
	@echo "All quality checks completed."

# Pre-commit hooks
pre-commit:
	@echo "Installing pre-commit hooks..."
	venv/bin/python -m pre_commit install
	@echo "Pre-commit hooks installed."

# Build and run
clean:
	@echo "Cleaning build artifacts..."
	rm -rf .build/
	rm -rf OpenDict.app/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "Cleaning completed."

clean-dist:
	@echo "Cleaning distribution artifacts..."
	rm -rf dist/
	rm -rf build/
	@echo "Distribution artifacts cleaned."

build:
	@echo "Building Swift application..."
	swift build -c release
	@echo "Build completed."

run-server:
	@echo "Starting Python transcription server..."
	venv/bin/python transcribe_server.py

run-app:
	@echo "Starting Swift application..."
	swift run OpenDict

# Documentation
docs:
	@echo "Generating documentation..."
	venv/bin/python -m sphinx-build -b html docs/ docs/_build/html/
	@echo "Documentation generated in docs/_build/html/"

# Distribution and packaging
dist: dist-release
	@echo "Distribution packages created!"

dist-dev:
	@echo "Building development distribution..."
	./scripts/build.sh --target development --format app --format zip
	@echo "Development distribution completed!"

dist-release:
	@echo "Building release distribution..."
	./scripts/build.sh --target release --format app --format dmg --format zip
	@echo "Release distribution completed!"

package:
	@echo "Creating installation packages..."
	python3 build.py --target release --format dmg --format zip
	@echo "Installation packages created!"

# Development shortcuts
dev-setup: setup install pre-commit
	@echo "Development environment ready!"

dev-test: format lint type-check test
	@echo "Development testing completed!"

# CI/CD targets
ci-test: install test-coverage quality-check
	@echo "CI testing completed!"

ci-build: install build
	@echo "CI build completed!"

# Check if virtual environment exists
check-venv:
	@if [ ! -d "venv" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi

# Override targets to check for venv
test lint format type-check security-check: check-venv
