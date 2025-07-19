#!/bin/bash
# Test script for infrastructure validation

set -euo pipefail

echo "🔍 Running infrastructure validation tests..."

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Test 1: Check for Terraform syntax errors (basic validation)
echo "Test 1: Checking Terraform syntax..."
syntax_error=false
for tf_file in *.tf; do
    if [[ -f "$tf_file" ]]; then
        # Basic syntax check - look for unmatched braces
        if ! python3 -c "
import re
with open('$tf_file', 'r') as f:
    content = f.read()
    # Remove comments and strings to avoid false positives
    content = re.sub(r'#.*', '', content)
    content = re.sub(r'\"[^\"]*\"', '\"\"', content)
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        raise ValueError(f'Unmatched braces in $tf_file: {open_braces} open, {close_braces} close')
" 2>/dev/null; then
            echo "❌ Syntax error in $tf_file"
            syntax_error=true
        fi
    fi
done

if [[ "$syntax_error" == "false" ]]; then
    echo "✅ Terraform syntax check passed"
else
    exit 1
fi

# Test 2: Check Terraform file structure
echo "Test 2: Checking Terraform file structure..."
if grep -q "terraform {" versions.tf && grep -q "required_providers" versions.tf; then
    echo "✅ Terraform configuration structure is valid"
else
    echo "❌ Invalid Terraform configuration structure"
    exit 1
fi

# Test 3: Check required files exist
echo "Test 3: Checking required files..."
required_files=(
    "main.tf"
    "variables.tf"
    "outputs.tf"
    "versions.tf"
    ".terraform-version"
    ".gitignore"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ Required file exists: $file"
    else
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

# Test 4: Check for sensitive data in files
echo "Test 4: Checking for sensitive data..."
sensitive_patterns=(
    "AKIA[0-9A-Z]{16}"  # AWS Access Key
    "[0-9a-zA-Z/+]{40}" # AWS Secret Key pattern
    "password.*="       # Password variables
    "secret.*="         # Secret variables
)

for pattern in "${sensitive_patterns[@]}"; do
    if grep -r -i "$pattern" . --exclude-dir=.terraform --exclude="*.tfstate*" --exclude="test_infrastructure.sh"; then
        echo "❌ Potential sensitive data found matching pattern: $pattern"
        exit 1
    fi
done
echo "✅ No sensitive data patterns found"

# Test 5: Validate GitHub Actions workflow syntax
echo "Test 5: Validating GitHub Actions workflow..."
workflow_file="../.github/workflows/infrastructure.yml"
if [[ -f "$workflow_file" ]]; then
    # Basic YAML syntax check
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; yaml.safe_load(open('$workflow_file'))" 2>/dev/null
        echo "✅ GitHub Actions workflow YAML is valid"
    else
        echo "⚠️  Python3 not available for YAML validation, skipping"
    fi
else
    echo "❌ GitHub Actions workflow file not found: $workflow_file"
    exit 1
fi

echo ""
echo "🎉 All infrastructure validation tests passed!"