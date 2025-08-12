#!/bin/bash
set -e

# Build Documentation Script
# Generates API documentation and builds the static site

echo "📚 Building Hoopstat Haus Shared Libraries Documentation"
echo "========================================================"

# Change to repository root
cd "$(dirname "$0")/.."

# Generate API documentation from libraries
echo ""
echo "🔍 Generating API documentation from shared libraries..."
python3 scripts/generate-docs.py

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to generate API documentation"
    exit 1
fi

echo "✅ API documentation generated successfully"

# Build the documentation site
echo ""
echo "🏗️  Building documentation site..."
mkdocs build

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to build documentation site"
    exit 1
fi

echo "✅ Documentation site built successfully"
echo ""
echo "📂 Documentation files are in: ./site/"
echo "🌐 To serve locally, run: mkdocs serve"
echo "🚀 Documentation ready for deployment!"