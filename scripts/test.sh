#!/bin/bash

# Run all tests with coverage reporting

set -e  # Exit on error

echo "🧪 Running tests..."

# Activate virtual environment if it exists
if [ -d ".lvenv" ]; then
    source .lvenv/bin/activate
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Please install development dependencies:"
    echo "   pip install -r requirements-dev.txt"
    exit 1
fi

# Run tests with coverage
echo "📊 Running tests with coverage..."
pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    -v \
    "$@"

echo ""
echo "📈 Coverage report generated:"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo ""
echo "✨ Tests complete!"
