#!/bin/bash
# Test script for ADR status checking functionality
# This script validates that the CI ADR check logic works correctly

set -euo pipefail

echo "🔍 Running ADR status validation tests..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="/tmp/adr_test_$$"

# Create test directory
mkdir -p "$TEST_DIR"

# Function to extract status from ADR file (same as CI)
get_adr_status() {
    local file="$1"
    awk '/^---$/{flag++; next} flag==1 && /^status:/ {gsub(/^status: *"?/, ""); gsub(/"$/, ""); print; exit}' "$file"
}

# Test 1: Create an ADR with Accepted status
echo "Test 1: ADR with Accepted status should pass"
cat > "$TEST_DIR/test-accepted.md" << 'EOF'
---
title: "Test Accepted ADR"
status: "Accepted"
date: "2025-01-15"
---

Test content
EOF

status=$(get_adr_status "$TEST_DIR/test-accepted.md")
if [[ "$status" == "Accepted" ]]; then
    echo "✅ Test 1 passed: Accepted status parsed correctly"
else
    echo "❌ Test 1 failed: Expected 'Accepted', got '$status'"
    exit 1
fi

# Test 2: Create an ADR with Proposed status  
echo "Test 2: ADR with Proposed status should be detected"
cat > "$TEST_DIR/test-proposed.md" << 'EOF'
---
title: "Test Proposed ADR"
status: "Proposed"
date: "2025-01-15"
---

Test content
EOF

status=$(get_adr_status "$TEST_DIR/test-proposed.md")
if [[ "$status" == "Proposed" ]]; then
    echo "✅ Test 2 passed: Proposed status parsed correctly"
else
    echo "❌ Test 2 failed: Expected 'Proposed', got '$status'"
    exit 1
fi

# Test 3: Create an ADR with Deprecated status
echo "Test 3: ADR with Deprecated status should pass"
cat > "$TEST_DIR/test-deprecated.md" << 'EOF'
---
title: "Test Deprecated ADR"
status: "Deprecated"
date: "2025-01-15"
---

Test content
EOF

status=$(get_adr_status "$TEST_DIR/test-deprecated.md")
if [[ "$status" == "Deprecated" ]]; then
    echo "✅ Test 3 passed: Deprecated status parsed correctly"
else
    echo "❌ Test 3 failed: Expected 'Deprecated', got '$status'"
    exit 1
fi

# Test 4: Create an ADR with Superseded status
echo "Test 4: ADR with Superseded status should pass"
cat > "$TEST_DIR/test-superseded.md" << 'EOF'
---
title: "Test Superseded ADR"
status: "Superseded by ADR-123"
date: "2025-01-15"
---

Test content
EOF

status=$(get_adr_status "$TEST_DIR/test-superseded.md")
if [[ "$status" == "Superseded by ADR-123" ]]; then
    echo "✅ Test 4 passed: Superseded status parsed correctly"
else
    echo "❌ Test 4 failed: Expected 'Superseded by ADR-123', got '$status'"
    exit 1
fi

# Test 5: Verify existing repository ADRs all have valid status
echo "Test 5: Verify all existing repository ADRs have valid status"
if [[ -d "$REPO_ROOT/meta/adr" ]]; then
    invalid_found=false
    for adr_file in "$REPO_ROOT/meta/adr"/*.md; do
        if [[ -f "$adr_file" && "$(basename "$adr_file")" != "TEMPLATE.md" ]]; then
            filename=$(basename "$adr_file")
            status=$(get_adr_status "$adr_file")
            
            if [[ "$status" == "Proposed" ]]; then
                echo "❌ Found Proposed ADR in repository: $filename"
                invalid_found=true
            elif [[ "$status" != "Accepted" && "$status" != "Deprecated" && ! "$status" =~ ^Superseded ]]; then
                echo "⚠️  Unknown status '$status' in $filename"
            fi
        fi
    done
    
    if [[ "$invalid_found" == "true" ]]; then
        echo "❌ Test 5 failed: Found ADRs with invalid status"
        exit 1
    else
        echo "✅ Test 5 passed: All repository ADRs have valid status"
    fi
else
    echo "ℹ️  Test 5 skipped: No ADR directory found"
fi

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All ADR status validation tests passed!"