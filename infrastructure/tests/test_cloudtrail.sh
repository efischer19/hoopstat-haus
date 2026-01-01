#!/bin/bash
# Test script for CloudTrail configuration validation

set -euo pipefail

echo "🔍 Running CloudTrail configuration tests..."

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# Test 1: Verify CloudTrail resource exists
echo "Test 1: Checking CloudTrail trail resource..."
if grep -q 'resource "aws_cloudtrail" "bronze_s3_events"' main.tf; then
    echo "✅ CloudTrail trail resource exists"
else
    echo "❌ CloudTrail trail resource not found"
    exit 1
fi

# Test 2: Verify CloudTrail CloudWatch Log Group exists
echo "Test 2: Checking CloudWatch Log Group for CloudTrail..."
if grep -q 'resource "aws_cloudwatch_log_group" "cloudtrail"' main.tf; then
    echo "✅ CloudWatch Log Group for CloudTrail exists"
else
    echo "❌ CloudWatch Log Group for CloudTrail not found"
    exit 1
fi

# Test 3: Verify CloudTrail S3 bucket exists
echo "Test 3: Checking CloudTrail S3 bucket..."
if grep -q 'resource "aws_s3_bucket" "cloudtrail"' main.tf; then
    echo "✅ CloudTrail S3 bucket resource exists"
else
    echo "❌ CloudTrail S3 bucket resource not found"
    exit 1
fi

# Test 4: Verify CloudTrail IAM role exists
echo "Test 4: Checking CloudTrail IAM role for CloudWatch..."
if grep -q 'resource "aws_iam_role" "cloudtrail_cloudwatch"' main.tf; then
    echo "✅ CloudTrail IAM role exists"
else
    echo "❌ CloudTrail IAM role not found"
    exit 1
fi

# Test 5: Verify CloudTrail is configured for Bronze bucket
echo "Test 5: Verifying CloudTrail monitors Bronze bucket..."
if grep -A 20 'resource "aws_cloudtrail" "bronze_s3_events"' main.tf | grep -q 'aws_s3_bucket.bronze.arn'; then
    echo "✅ CloudTrail is configured to monitor Bronze bucket"
else
    echo "❌ CloudTrail not configured for Bronze bucket"
    exit 1
fi

# Test 6: Verify WriteOnly events are configured
echo "Test 6: Verifying WriteOnly event configuration..."
if grep -A 20 'resource "aws_cloudtrail" "bronze_s3_events"' main.tf | grep -q 'read_write_type.*=.*"WriteOnly"'; then
    echo "✅ CloudTrail configured for WriteOnly events"
else
    echo "❌ CloudTrail not configured for WriteOnly events"
    exit 1
fi

# Test 7: Verify CloudTrail CloudWatch Logs integration
echo "Test 7: Verifying CloudWatch Logs integration..."
if grep -A 20 'resource "aws_cloudtrail" "bronze_s3_events"' main.tf | grep -q 'cloud_watch_logs_group_arn'; then
    echo "✅ CloudTrail CloudWatch Logs integration configured"
else
    echo "❌ CloudTrail CloudWatch Logs integration not found"
    exit 1
fi

# Test 8: Verify Temporary tag on resources
echo "Test 8: Verifying Temporary tag for easy cleanup..."
temporary_tag_count=$(grep -c 'Temporary.*=.*"true"' main.tf || true)
if [[ "$temporary_tag_count" -ge 3 ]]; then
    echo "✅ CloudTrail resources tagged as temporary ($temporary_tag_count occurrences)"
else
    echo "❌ Not all CloudTrail resources have Temporary tag"
    exit 1
fi

# Test 9: Verify S3 bucket encryption for CloudTrail bucket
echo "Test 9: Verifying CloudTrail S3 bucket encryption..."
if grep -q 'resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail"' main.tf; then
    echo "✅ CloudTrail S3 bucket encryption configured"
else
    echo "❌ CloudTrail S3 bucket encryption not configured"
    exit 1
fi

# Test 10: Verify S3 bucket policy for CloudTrail
echo "Test 10: Verifying CloudTrail S3 bucket policy..."
if grep -q 'resource "aws_s3_bucket_policy" "cloudtrail"' main.tf; then
    echo "✅ CloudTrail S3 bucket policy configured"
else
    echo "❌ CloudTrail S3 bucket policy not configured"
    exit 1
fi

echo ""
echo "✅ All CloudTrail configuration tests passed!"
