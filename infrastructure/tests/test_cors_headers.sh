#!/bin/bash
# Test script for CloudFront CORS and public HTTP infrastructure validation
#
# Static tests (no AWS credentials needed):
#   ./test_cors_headers.sh
#
# Live CORS smoke test against a deployed CloudFront distribution:
#   ./test_cors_headers.sh --live <CLOUDFRONT_URL>
#   Example: ./test_cors_headers.sh --live https://d111111abcdef8.cloudfront.net/index/latest.json

set -euo pipefail

echo "🌐 Running CORS / public HTTP infrastructure validation tests..."

# Change to infrastructure directory
cd "$(dirname "$0")/.."

# ============================================================================
# Static validation (grep-based checks against Terraform files)
# ============================================================================

# Test 1: CloudFront cache behavior allows OPTIONS requests
echo "Test 1: Checking CloudFront allowed_methods includes OPTIONS..."
if grep -A 5 'default_cache_behavior' main.tf | grep -q 'OPTIONS'; then
    echo "✅ CloudFront allowed_methods includes OPTIONS"
else
    echo "❌ CloudFront allowed_methods missing OPTIONS"
    exit 1
fi

# Test 2: CORS response headers policy has origin_override = true
echo "Test 2: Checking CORS origin_override is true..."
if grep -A 20 'aws_cloudfront_response_headers_policy.*gold_artifacts_cors' main.tf \
    | grep -q 'origin_override.*=.*true'; then
    echo "✅ CORS origin_override is true"
else
    echo "❌ CORS origin_override is not true"
    exit 1
fi

# Test 3: CORS allows all origins (Access-Control-Allow-Origin: *)
echo "Test 3: Checking Access-Control-Allow-Origin allows all origins..."
if grep -A 25 'aws_cloudfront_response_headers_policy.*gold_artifacts_cors' main.tf \
    | grep -A 3 'access_control_allow_origins' | grep -q '"[*]"'; then
    echo "✅ Access-Control-Allow-Origin: * configured"
else
    echo "❌ Access-Control-Allow-Origin: * not configured"
    exit 1
fi

# Test 4: S3 bucket policy restricts access to served/* prefix only
echo "Test 4: Checking S3 bucket policy restricts to served/* prefix..."
if grep -A 20 'aws_s3_bucket_policy.*gold_cloudfront_read' main.tf \
    | grep -q '/served/\*'; then
    echo "✅ S3 bucket policy restricts access to served/* prefix"
else
    echo "❌ S3 bucket policy does not restrict to served/* prefix"
    exit 1
fi

# Test 5: S3 bucket policy only grants s3:GetObject (no write/delete)
echo "Test 5: Checking S3 bucket policy only grants s3:GetObject..."
policy_actions=$(grep -A 20 'aws_s3_bucket_policy.*gold_cloudfront_read' main.tf \
    | grep -oP '"s3:\w+"' || true)
if ! echo "$policy_actions" | grep -q '"s3:GetObject"'; then
    echo "❌ S3 bucket policy missing s3:GetObject action"
    exit 1
fi
action_count=$(echo "$policy_actions" | grep -c '"s3:' || true)
if [[ "$action_count" -ne 1 ]]; then
    echo "❌ S3 bucket policy grants actions beyond s3:GetObject (found $action_count actions)"
    exit 1
fi
echo "✅ S3 bucket policy only grants s3:GetObject"

# Test 6: CloudFront OAC is the only access path (bucket is fully private)
echo "Test 6: Checking Gold bucket public access is fully blocked..."
block_count=$(grep -A 8 'aws_s3_bucket_public_access_block.*gold"' main.tf \
    | grep -c 'true' || true)
if [[ "$block_count" -eq 4 ]]; then
    echo "✅ Gold bucket has all four public access blocks enabled"
else
    echo "❌ Gold bucket public access block is incomplete (found $block_count of 4)"
    exit 1
fi

# Test 7: Origin request policy forwards CORS headers (CORS-S3Origin)
echo "Test 7: Checking origin request policy forwards CORS headers..."
if grep -A 15 'default_cache_behavior' main.tf \
    | grep -q 'origin_request_policy_id'; then
    echo "✅ Origin request policy is configured (CORS headers forwarded to S3)"
else
    echo "❌ Missing origin_request_policy_id — Origin header will be stripped by CachingOptimized"
    exit 1
fi

# Test 8: CORS response headers allow OPTIONS method
echo "Test 8: Checking CORS allows OPTIONS method in response headers..."
if grep -A 25 'aws_cloudfront_response_headers_policy.*gold_artifacts_cors' main.tf \
    | grep -A 3 'access_control_allow_methods' | grep -q 'OPTIONS'; then
    echo "✅ CORS response allows OPTIONS method"
else
    echo "❌ CORS response missing OPTIONS method"
    exit 1
fi

echo ""
echo "🎉 All static CORS infrastructure validation tests passed!"
echo "📋 Summary:"
echo "   ✅ CloudFront allows GET, HEAD, OPTIONS methods"
echo "   ✅ CORS origin_override = true"
echo "   ✅ Access-Control-Allow-Origin: * configured"
echo "   ✅ S3 bucket policy restricted to served/* prefix"
echo "   ✅ S3 bucket policy only grants s3:GetObject"
echo "   ✅ Gold bucket is fully private (OAC-only access)"
echo "   ✅ Origin request policy forwards CORS headers to S3"
echo "   ✅ CORS response allows OPTIONS method"

# ============================================================================
# Live smoke test (requires --live flag and a CloudFront URL)
# ============================================================================

if [[ "${1:-}" == "--live" ]]; then
    LIVE_URL="${2:-}"
    if [[ -z "$LIVE_URL" ]]; then
        echo ""
        echo "❌ Usage: $0 --live <CLOUDFRONT_URL>"
        echo "   Example: $0 --live https://d111111abcdef8.cloudfront.net/index/latest.json"
        exit 1
    fi

    echo ""
    echo "🔬 Running live CORS smoke test against: $LIVE_URL"
    echo ""

    # Send an OPTIONS preflight request and capture headers
    echo "Sending: curl -s -I -X OPTIONS -H 'Origin: https://example.com' $LIVE_URL"
    RESPONSE=$(curl -s -I -X OPTIONS \
        -H "Origin: https://example.com" \
        -H "Access-Control-Request-Method: GET" \
        "$LIVE_URL" 2>&1) || true

    echo "$RESPONSE"
    echo ""

    # Check for CORS headers in the response
    if echo "$RESPONSE" | grep -qi 'access-control-allow-origin'; then
        echo "✅ Live test: Access-Control-Allow-Origin header present"
    else
        echo "❌ Live test: Access-Control-Allow-Origin header missing"
        exit 1
    fi

    if echo "$RESPONSE" | grep -qi 'access-control-allow-methods'; then
        echo "✅ Live test: Access-Control-Allow-Methods header present"
    else
        echo "❌ Live test: Access-Control-Allow-Methods header missing"
        exit 1
    fi

    echo ""
    echo "🎉 Live CORS smoke test passed!"
fi
