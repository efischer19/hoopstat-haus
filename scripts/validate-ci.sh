#!/bin/bash
# CI Validation Script - Simulates the enhanced CI pipeline locally

set -e

echo "🚀 Starting Build and Test Orchestration Validation"
echo "=================================================="

# Simulate change detection
echo ""
echo "📊 Change Detection Phase"
echo "------------------------"

# Check for libraries
if [ -d "libs" ] && [ "$(find libs -name '*.py' -o -name 'pyproject.toml' | wc -l)" -gt 0 ]; then
    echo "✅ Found shared libraries in /libs"
    HAS_LIB_CHANGES=true
    LIBS=$(find libs -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
    echo "Libraries: $LIBS"
else
    echo "ℹ️  No shared libraries found"
    HAS_LIB_CHANGES=false
fi

# Check for applications  
if [ -d "apps" ] && [ "$(find apps -name '*.py' -o -name 'pyproject.toml' | wc -l)" -gt 0 ]; then
    echo "✅ Found applications in /apps"
    HAS_APP_CHANGES=true
    APPS=$(find apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
    echo "Applications: $APPS"
else
    echo "ℹ️  No applications found"
    HAS_APP_CHANGES=false
fi

# Test Libraries Phase
if [ "$HAS_LIB_CHANGES" = true ]; then
    echo ""
    echo "📚 Library Testing Phase"
    echo "------------------------"
    
    for lib in $LIBS; do
        if [ -f "libs/$lib/pyproject.toml" ]; then
            echo "Testing library: $lib"
            cd "libs/$lib"
            
            echo "  🔍 Format check..."
            poetry run ruff format --check . || { echo "❌ Format check failed for $lib"; exit 1; }
            
            echo "  🔍 Lint check..."
            poetry run ruff check . || { echo "❌ Lint check failed for $lib"; exit 1; }
            
            echo "  🧪 Running tests..."
            poetry run pytest || { echo "❌ Tests failed for $lib"; exit 1; }
            
            echo "  ✅ Library $lib passed all tests"
            echo "  📦 Library is ready for use by applications"
            
            cd - > /dev/null
        fi
    done
fi

# Test Applications Phase
if [ "$HAS_APP_CHANGES" = true ]; then
    echo ""
    echo "🚀 Application Testing Phase"
    echo "----------------------------"
    
    for app in $APPS; do
        if [ -f "apps/$app/pyproject.toml" ]; then
            echo "Testing application: $app"
            cd "apps/$app"
            
            echo "  🔍 Format check..."
            poetry run ruff format --check . || { echo "❌ Format check failed for $app"; exit 1; }
            
            echo "  🔍 Lint check..."
            poetry run ruff check . || { echo "❌ Lint check failed for $app"; exit 1; }
            
            echo "  🧪 Running tests..."
            poetry run pytest || { echo "❌ Tests failed for $app"; exit 1; }
            
            # Check deployment type
            if [ -f "Dockerfile" ]; then
                echo "  🚢 Application $app is deployable (has Dockerfile)"
                echo "  🔍 Checking for shared library dependencies..."
                
                if grep -q "path.*\\.\\./\\.\\./libs" pyproject.toml; then
                    echo "  📦 Application uses shared libraries"
                    echo "  ℹ️  Note: Docker build would use repository root context"
                    # In real CI: docker build -f apps/$app/Dockerfile -t $app:ci ../../
                else
                    echo "  📦 Standalone application"
                    # In real CI: docker build -t $app:ci .
                fi
                echo "  ✅ Docker build validation passed (simulated)"
                echo "  🚢 Application is ready for deployment"
            else
                echo "  🛠️  Application $app is a utility/tool (no Dockerfile required)"
                echo "  ✅ Utility/tool application validated successfully"
            fi
            
            cd - > /dev/null
        fi
    done
fi

# Integration Testing Phase
if [ "$HAS_LIB_CHANGES" = true ] && [ "$HAS_APP_CHANGES" = true ]; then
    echo ""
    echo "🔗 Integration Testing Phase"
    echo "---------------------------"
    
    for app in $APPS; do
        if [ -f "apps/$app/pyproject.toml" ]; then
            echo "Testing integration for application: $app"
            cd "apps/$app"
            
            echo "  🔗 Testing $app with updated libraries..."
            poetry run pytest || { echo "❌ Integration testing failed for $app"; exit 1; }
            echo "  ✅ Integration testing passed for $app"
            echo "  🔗 Application works correctly with updated shared libraries"
            
            cd - > /dev/null
        fi
    done
fi

echo ""
echo "🎉 All CI/CD pipeline phases completed successfully!"
echo "=================================================="
echo "Summary:"
echo "- Libraries tested: $([ "$HAS_LIB_CHANGES" = true ] && echo "✅" || echo "➖")"
echo "- Applications tested: $([ "$HAS_APP_CHANGES" = true ] && echo "✅" || echo "➖")"
echo "- Integration tested: $([ "$HAS_LIB_CHANGES" = true ] && [ "$HAS_APP_CHANGES" = true ] && echo "✅" || echo "➖")"
echo ""
echo "✅ Build and Test Orchestration validation complete!"