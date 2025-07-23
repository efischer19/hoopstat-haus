#!/bin/bash
set -e

# Local CI Check Script
# Runs the same quality checks that CI runs for a given Python project
# Usage: ./scripts/local-ci-check.sh <path-to-app-or-lib>

if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide the path to an app or library"
    echo "Usage: $0 <path-to-app-or-lib>"
    echo "Examples:"
    echo "  $0 apps/example-calculator-app"
    echo "  $0 libs/hoopstat-config"
    exit 1
fi

PROJECT_PATH="$1"

# Check if the path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Error: Directory '$PROJECT_PATH' does not exist"
    exit 1
fi

# Check if it's a Python project
if [ ! -f "$PROJECT_PATH/pyproject.toml" ]; then
    echo "❌ Error: '$PROJECT_PATH' is not a Python project (no pyproject.toml found)"
    exit 1
fi

echo "🔍 Running local CI checks for: $PROJECT_PATH"
echo "=================================================="

# Navigate to the project directory
cd "$PROJECT_PATH"

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed. Please install Poetry first."
    exit 1
fi

echo "📦 Installing dependencies..."
poetry install

echo ""
echo "🎨 Checking code formatting..."
poetry run ruff format --check .
if [ $? -eq 0 ]; then
    echo "✅ Format check passed"
else
    echo "❌ Format check failed. Run 'poetry run ruff format .' to fix formatting issues."
    exit 1
fi

echo ""
echo "🧹 Running linter..."
poetry run ruff check .
if [ $? -eq 0 ]; then
    echo "✅ Lint check passed"
else
    echo "❌ Lint check failed. Please fix the linting issues above."
    exit 1
fi

echo ""
echo "🧪 Running tests..."
poetry run pytest
if [ $? -eq 0 ]; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed. Please fix the failing tests."
    exit 1
fi

echo ""
echo "✅ All local CI checks passed for $PROJECT_PATH!"
echo "🚀 Your code is ready for CI and review."