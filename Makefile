# EcoFlow API Linting Makefile
# Usage: make [command]

.PHONY: help lint format check fix type-check security all install clean

# Default target
help:
	@echo "🚀 EcoFlow API Linting Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  lint        - Run ruff linting (check only)"
	@echo "  format      - Format code with ruff"
	@echo "  check       - Run all checks (lint + format check)"
	@echo "  fix         - Fix auto-fixable issues"
	@echo "  type-check  - Run mypy type checking"
	@echo "  security    - Run bandit security check"
	@echo "  all         - Run all linting tools"
	@echo "  install     - Install linting dependencies"
	@echo "  clean       - Clean cache files"
	@echo ""
	@echo "Usage examples:"
	@echo "  make lint"
	@echo "  make fix"
	@echo "  make all"

# Linting with ruff (check only)
lint:
	@echo "🔍 Running ruff linting..."
	python -m ruff check custom_components/ --no-fix

# Format code with ruff
format:
	@echo "📝 Formatting code with ruff..."
	python -m ruff format custom_components/

# Run all checks (lint + format check)
check:
	@echo "🔍 Running comprehensive checks..."
	@echo "Running ruff lint..." && python -m ruff check custom_components/ --no-fix && \
	echo "Checking format..." && python -m ruff format custom_components/ --check && \
	echo "✅ All checks passed!"

# Fix auto-fixable issues
fix:
	@echo "🔧 Fixing auto-fixable issues..."
	@echo "Running ruff fix..." && python -m ruff check custom_components/ --fix && \
	echo "Formatting code..." && python -m ruff format custom_components/ && \
	echo "✅ All issues fixed!"

# Type checking with mypy
type-check:
	@echo "🔍 Running mypy type checking..."
	python -m mypy custom_components/

# Security check with bandit
security:
	@echo "🔒 Running bandit security check..."
	python -m bandit -r custom_components/

# Run all linting tools
all:
	@echo "🚀 Running all linting tools..."
	@echo "📝 1. Formatting check..." && python -m ruff format custom_components/ --check && \
	echo "🔍 2. Linting..." && python -m ruff check custom_components/ --no-fix && \
	echo "🔍 3. Type checking..." && python -m mypy custom_components/ && \
	echo "🔒 4. Security check..." && python -m bandit -r custom_components/ && \
	echo "✅ All checks passed!"

# Install linting dependencies
install:
	@echo "📦 Installing linting dependencies..."
	python -m pip install --upgrade pip
	python -m pip install -r requirements-lint.txt
	python -m pre_commit install
	@echo "✅ Installation complete!"

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cache cleaned!"

# Quick development check (lint + format)
dev: lint format
	@echo "✅ Development checks complete!"

# Pre-commit check
pre-commit:
	@echo "🔍 Running pre-commit checks..."
	python -m pre_commit run --all-files
