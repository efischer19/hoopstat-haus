#!/bin/bash
set -e

# Documentation Check Script
# Validates that documentation is complete for all shared libraries

echo "📚 Checking documentation completeness for shared libraries"
echo "=========================================================="

# Change to repository root
cd "$(dirname "$0")/.."

LIBS_DIR="libs"
DOCS_DIR="docs-src/libraries"

if [ ! -d "$LIBS_DIR" ]; then
    echo "❌ Error: $LIBS_DIR directory does not exist"
    exit 1
fi

if [ ! -d "$DOCS_DIR" ]; then
    echo "❌ Error: $DOCS_DIR directory does not exist"
    echo "Run './scripts/build-docs.sh' to generate documentation"
    exit 1
fi

# Check each library
missing_docs=()
for lib_path in "$LIBS_DIR"/*; do
    if [ -d "$lib_path" ]; then
        lib_name=$(basename "$lib_path")
        doc_file="$DOCS_DIR/${lib_name}.md"
        
        if [ -f "$doc_file" ]; then
            echo "✅ Documentation exists for $lib_name"
            
            # Check if documentation is not empty
            if [ ! -s "$doc_file" ]; then
                echo "⚠️  Warning: Documentation for $lib_name is empty"
            fi
        else
            echo "❌ Missing documentation for $lib_name"
            missing_docs+=("$lib_name")
        fi
    fi
done

if [ ${#missing_docs[@]} -eq 0 ]; then
    echo ""
    echo "✅ All shared libraries have documentation!"
    exit 0
else
    echo ""
    echo "❌ Missing documentation for the following libraries:"
    for lib in "${missing_docs[@]}"; do
        echo "   - $lib"
    done
    echo ""
    echo "Run './scripts/build-docs.sh' to generate missing documentation"
    exit 1
fi