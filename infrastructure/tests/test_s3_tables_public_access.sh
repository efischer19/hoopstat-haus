#!/bin/bash
# Test script for S3 Tables public access configuration validation

set -euo pipefail

echo "🏀 Running S3 Tables public access configuration tests..."

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Test 1: Check for S3 Tables bucket policy resource
echo "Test 1: Checking for S3 Tables bucket policy configuration..."
if grep -q "aws_s3tables_table_bucket_policy" main.tf; then
    echo "✅ Found S3 Tables bucket policy resource"
else
    echo "❌ Missing S3 Tables bucket policy resource"
    exit 1
fi

# Test 2: Verify public read permissions in bucket policy
echo "Test 2: Checking for public read permissions..."
required_actions=(
    "s3tables:GetTable"
    "s3tables:GetTableData" 
    "s3tables:GetTableMetadata"
    "s3tables:ListTables"
    "s3tables:GetTableBucket"
)

for action in "${required_actions[@]}"; do
    if grep -q "$action" main.tf; then
        echo "✅ Found required action: $action"
    else
        echo "❌ Missing required action: $action"
        exit 1
    fi
done

# Test 3: Check for Principal "*" (anonymous access)
echo "Test 3: Checking for anonymous access configuration..."
if grep -A 20 "aws_s3tables_table_bucket_policy" main.tf | grep -q 'Principal = "\*"'; then
    echo "✅ Found anonymous Principal configuration"
else
    echo "❌ Missing anonymous Principal configuration"
    exit 1
fi

# Test 4: Verify outputs include public access information
echo "Test 4: Checking outputs for public access configuration..."
if grep -q "public_access" outputs.tf; then
    echo "✅ Found public access configuration in outputs"
else
    echo "❌ Missing public access configuration in outputs"
    exit 1
fi

# Test 5: Check for MCP server configuration in outputs
echo "Test 5: Checking for MCP server configuration..."
if grep -q "mcp_server_config" outputs.tf; then
    echo "✅ Found MCP server configuration in outputs"
else
    echo "❌ Missing MCP server configuration in outputs"
    exit 1
fi

# Test 6: Verify no AWS credentials needed for public access
echo "Test 6: Checking that AWS credentials are not required..."
if ! grep -A 10 "mcp_server_config" outputs.tf | grep -q "AWS_ACCESS_KEY\|AWS_SECRET"; then
    echo "✅ No AWS credentials required in MCP configuration"
else
    echo "❌ AWS credentials found in MCP configuration (should not be needed for public access)"
    exit 1
fi

# Test 7: Check for dependency configuration
echo "Test 7: Checking for proper dependencies..."
if grep -A 5 "depends_on" main.tf | grep -q "aws_s3tables_table_bucket.gold_tables"; then
    echo "✅ Found proper bucket policy dependencies"
else
    echo "❌ Missing proper bucket policy dependencies"
    exit 1
fi

# Test 8: Validate bucket policy has required conditions
echo "Test 8: Checking for security conditions..."
if grep -A 25 "aws_s3tables_table_bucket_policy" main.tf | grep -q "Condition"; then
    echo "✅ Found security conditions in bucket policy"
else
    echo "❌ Missing security conditions in bucket policy"
    exit 1
fi

echo ""
echo "🎉 All S3 Tables public access configuration tests passed!"
echo "📋 Summary:"
echo "   ✅ S3 Tables bucket policy configured for public read access"
echo "   ✅ Required S3 Tables actions included (GetTable, GetTableData, etc.)"
echo "   ✅ Anonymous access properly configured with Principal '*'"
echo "   ✅ Public access information included in outputs"
echo "   ✅ MCP server configuration available without AWS credentials"
echo "   ✅ Security conditions applied to bucket policy"
echo "   ✅ Proper resource dependencies configured"
echo ""
echo "🏀 Basketball analytics data is ready for public MCP access!"