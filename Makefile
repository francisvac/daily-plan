# ZeroClaw Baby Planner - Testing Makefile
# Comprehensive testing commands for the baby planner system

.PHONY: help test test-unit test-integration test-e2e test-feedback test-memory test-coverage test-clean lint format

# Default target
help:
	@echo "ZeroClaw Baby Planner - Testing Commands"
	@echo "======================================="
	@echo ""
	@echo "Testing Commands:"
	@echo "  test              Run all tests"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-e2e          Run end-to-end tests only"
	@echo "  test-feedback     Run feedback processing tests"
	@echo "  test-memory       Run memory management tests"
	@echo "  test-coverage     Run tests with coverage report"
	@echo "  test-watch        Run tests in watch mode"
	@echo "  test-failed       Run only failed tests from last run"
	@echo ""
	@echo "Quality Commands:"
	@echo "  lint              Run code linting"
	@echo "  format            Format code with black"
	@echo "  type-check        Run type checking"
	@echo ""
	@echo "Utility Commands:"
	@echo "  test-clean        Clean test artifacts"
	@echo "  setup-test        Set up test environment"
	@echo "  test-docker       Run tests in Docker container"

# Test commands
test:
	@echo "Running all tests..."
	python3 -m pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	python3 -m pytest tests/unit/ -v -m "unit"

test-integration:
	@echo "Running integration tests..."
	python3 -m pytest tests/integration/ -v -m "integration"

test-e2e:
	@echo "Running end-to-end tests..."
	python3 -m pytest tests/end_to_end/ -v -m "e2e"

test-feedback:
	@echo "Running feedback processing tests..."
	python3 -m pytest tests/ -v -m "feedback" -k "feedback"

test-memory:
	@echo "Running memory management tests..."
	python3 -m pytest tests/ -v -m "memory" -k "memory"

test-coverage:
	@echo "Running tests with coverage..."
	python3 -m pytest tests/ --cov=daily_plans --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-watch:
	@echo "Running tests in watch mode..."
	python3 -m pytest tests/ --watch

test-failed:
	@echo "Running only failed tests from last run..."
	python3 -m pytest tests/ --lf

# Quality commands
lint:
	@echo "Running code linting..."
	python3 -m flake8 daily_plans/ tests/ --max-line-length=120 --ignore=E203,W503
	python3 -m pylint daily_plans/ --disable=C0114,C0115,C0116

format:
	@echo "Formatting code..."
	python3 -m black daily_plans/ tests/ --line-length=120

type-check:
	@echo "Running type checking..."
	python3 -m mypy daily_plans/ --ignore-missing-imports

# Utility commands
test-clean:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

setup-test:
	@echo "Setting up test environment..."
	python3 -m pip install -r requirements.txt
	python3 -m pip install pytest pytest-mock pytest-cov pytest-asyncio
	python3 -m pip install flake8 pylint black mypy

test-docker:
	@echo "Running tests in Docker container..."
	docker build -t baby-planner-test -f Dockerfile.test .
	docker run --rm baby-planner-test

# Performance testing
test-performance:
	@echo "Running performance tests..."
	python3 -m pytest tests/ -v -m "performance" --benchmark-only

# Security testing
test-security:
	@echo "Running security tests..."
	python3 -m bandit -r daily_plans/
	python3 -m safety check

# Documentation testing
test-docs:
	@echo "Running documentation tests..."
	python3 -m doctest daily_plans/*.py

# Parallel testing
test-parallel:
	@echo "Running tests in parallel..."
	python3 -m pytest tests/ -n auto

# Specific component testing
test-email:
	@echo "Running email integration tests..."
	python3 -m pytest tests/ -v -m "email" -k "email"

test-patterns:
	@echo "Running pattern learning tests..."
	python3 -m pytest tests/ -v -m "patterns" -k "patterns"

# Continuous integration friendly commands
test-ci:
	@echo "Running CI-friendly tests..."
	python3 -m pytest tests/ --cov=daily_plans --cov-report=xml --junit-xml=test-results.xml

# Development workflow
dev-test: test-unit lint
	@echo "Development test cycle completed"

full-test: test lint type-check test-security
	@echo "Full test suite completed"

# Quick verification
quick-test:
	@echo "Running quick verification tests..."
	python3 -m pytest tests/unit/test_memory_manager.py::TestMemoryManager::test_memory_manager_initialization -v
	python3 -m pytest tests/unit/test_email_command_processor.py::TestEmailCommandProcessor::test_processor_initialization -v

# Report generation
test-report:
	@echo "Generating test report..."
	python3 -m pytest tests/ --html=test-report.html --self-contained-html
	@echo "Test report generated: test-report.html"

# Environment setup
setup-dev:
	@echo "Setting up development environment..."
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt
	pre-commit install
