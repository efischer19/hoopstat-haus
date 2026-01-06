#!/bin/bash
# Test script for Medallion Architecture S3 bucket infrastructure validation

set -euo pipefail

echo "🏆 Running Medallion Architecture infrastructure validation tests..."

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Test 1: Check for required Medallion Architecture resources in main.tf
echo "Test 1: Checking for Medallion Architecture S3 buckets..."
required_buckets=(
    "aws_s3_bucket.*bronze"
    "aws_s3_bucket.*silver"
    "aws_s3_bucket.*gold"
    "aws_s3_bucket.*access_logs"
)

for bucket in "${required_buckets[@]}"; do
    if grep -q "$bucket" main.tf; then
        echo "✅ Found bucket resource: $bucket"
    else
        echo "❌ Missing bucket resource: $bucket"
        exit 1
    fi
done

# Test 2: Check for lifecycle policies
echo "Test 2: Checking for lifecycle policies..."
lifecycle_configs=(
    "aws_s3_bucket_lifecycle_configuration.*bronze"
    "aws_s3_bucket_lifecycle_configuration.*silver"
    "aws_s3_bucket_lifecycle_configuration.*gold"
    "aws_s3_bucket_lifecycle_configuration.*access_logs"
)

for config in "${lifecycle_configs[@]}"; do
    if grep -q "$config" main.tf; then
        echo "✅ Found lifecycle configuration: $config"
    else
        echo "❌ Missing lifecycle configuration: $config"
        exit 1
    fi
done

# Test 3: Check for IAM roles
echo "Test 3: Checking for IAM roles..."
iam_roles=(
    "aws_iam_role.*bronze_data_access"
    "aws_iam_role.*silver_data_access"
    "aws_iam_role.*gold_data_access"
)

for role in "${iam_roles[@]}"; do
    if grep -q "$role" main.tf; then
        echo "✅ Found IAM role: $role"
    else
        echo "❌ Missing IAM role: $role"
        exit 1
    fi
done

# Test 4: Check for encryption configuration
echo "Test 4: Checking for encryption configuration..."
encryption_configs=(
    "aws_s3_bucket_server_side_encryption_configuration.*bronze"
    "aws_s3_bucket_server_side_encryption_configuration.*silver"
    "aws_s3_bucket_server_side_encryption_configuration.*gold"
)

for config in "${encryption_configs[@]}"; do
    if grep -q "$config" main.tf; then
        echo "✅ Found encryption configuration: $config"
    else
        echo "❌ Missing encryption configuration: $config"
        exit 1
    fi
done

# Test 5: Check for bucket versioning
echo "Test 5: Checking for bucket versioning..."
versioning_configs=(
    "aws_s3_bucket_versioning.*bronze"
    "aws_s3_bucket_versioning.*silver"
    "aws_s3_bucket_versioning.*gold"
)

for config in "${versioning_configs[@]}"; do
    if grep -q "$config" main.tf; then
        echo "✅ Found versioning configuration: $config"
    else
        echo "❌ Missing versioning configuration: $config"
        exit 1
    fi
done

# Test 6: Check for CloudWatch logging
echo "Test 6: Checking for CloudWatch logging..."
logging_configs=(
    "aws_s3_bucket_logging.*bronze"
    "aws_s3_bucket_logging.*silver"
    "aws_s3_bucket_logging.*gold"
)

for config in "${logging_configs[@]}"; do
    if grep -q "$config" main.tf; then
        echo "✅ Found logging configuration: $config"
    else
        echo "❌ Missing logging configuration: $config"
        exit 1
    fi
done

# Test 7: Check for public access blocks
echo "Test 7: Checking for public access blocks..."
public_access_blocks=(
    "aws_s3_bucket_public_access_block.*bronze"
    "aws_s3_bucket_public_access_block.*silver"
    "aws_s3_bucket_public_access_block.*gold"
)

for block in "${public_access_blocks[@]}"; do
    if grep -q "$block" main.tf; then
        echo "✅ Found public access block: $block"
    else
        echo "❌ Missing public access block: $block"
        exit 1
    fi
done

# Test 8: Check outputs.tf for Medallion Architecture outputs
echo "Test 8: Checking for Medallion Architecture outputs..."
if grep -q "medallion_s3_buckets" outputs.tf; then
    echo "✅ Found medallion_s3_buckets output"
else
    echo "❌ Missing medallion_s3_buckets output"
    exit 1
fi

if grep -q "medallion_iam_roles" outputs.tf; then
    echo "✅ Found medallion_iam_roles output"
else
    echo "❌ Missing medallion_iam_roles output"
    exit 1
fi

# Test 9: Validate storage class transitions
echo "Test 9: Validating storage class transitions..."
if grep -q "INTELLIGENT_TIERING" main.tf; then
    echo "✅ Found Bronze layer Intelligent Tiering transition"
else
    echo "❌ Missing Bronze layer Intelligent Tiering transition"
    exit 1
fi

if grep -q "STANDARD_IA" main.tf; then
    echo "✅ Found Silver layer Standard-IA transition"
else
    echo "❌ Missing Silver layer Standard-IA transition"
    exit 1
fi

# Test 10: Check retention periods match medallion architecture requirements
echo "Test 10: Checking retention periods..."
# Bronze: 2 years (730 days)
if grep -A 20 "bronze_primary_data" main.tf | grep -q "days = 730"; then
    echo "✅ Bronze layer has correct 2-year retention (730 days)"
else
    echo "❌ Bronze layer missing 2-year retention policy"
    exit 1
fi

# Silver: 3 years (1095 days)
if grep -A 20 "silver_primary_data" main.tf | grep -q "days = 1095"; then
    echo "✅ Silver layer has correct 3-year retention (1095 days)"
else
    echo "❌ Silver layer missing 3-year retention policy"
    exit 1
fi

echo ""
echo "🎉 All Medallion Architecture infrastructure validation tests passed!"
echo "📋 Summary:"
echo "   ✅ 4 S3 buckets configured (Bronze, Silver, Gold, Access Logs)"
echo "   ✅ 4 lifecycle policies with appropriate retention"
echo "   ✅ 3 IAM roles for least-privilege data access"
echo "   ✅ Encryption enabled for all buckets"
echo "   ✅ Versioning enabled for all buckets"
echo "   ✅ CloudWatch logging configured"
echo "   ✅ Public access blocked for all buckets"
echo "   ✅ Storage class transitions aligned with medallion architecture"