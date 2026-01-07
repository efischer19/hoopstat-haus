# Public Access Guide for JSON Artifacts

**Status:** Production  
**Last Updated:** 2026-01-07  
**Related ADRs:** [ADR-028](../meta/adr/ADR-028-gold_layer_final.md)

## Overview

This guide documents the public access configuration for JSON artifacts served from the Gold layer S3 bucket via CloudFront. The infrastructure uses CloudFront with Origin Access Control (OAC) to enable secure public access while keeping the S3 bucket private.

## Architecture

```
Browser/App
    ↓
CloudFront Distribution (HTTPS, edge caching, CORS)
    ↓
CloudFront OAC (signed requests)
    ↓
S3 Gold Bucket (private, served/ prefix only)
    └── served/
        ├── player_daily/{date}/{player_id}.json
        ├── team_daily/{date}/{team_id}.json
        ├── top_lists/{date}/{metric}.json
        └── index/latest.json
```

## Access Method

### CloudFront Distribution

**Base URL:** `https://<cloudfront-domain>.cloudfront.net`

The exact CloudFront domain is available from Terraform outputs:
```bash
cd infrastructure
terraform output cloudfront_distribution
```

**Example URLs:**
```
https://<cloudfront-domain>.cloudfront.net/player_daily/2024-11-15/2544.json
https://<cloudfront-domain>.cloudfront.net/team_daily/2024-11-15/1610612747.json
https://<cloudfront-domain>.cloudfront.net/top_lists/2024-11-15/top_scorers.json
https://<cloudfront-domain>.cloudfront.net/index/latest.json
```

**Features:**
- HTTPS access via CloudFront edge locations
- Global edge caching for low latency
- CORS enabled for browser compatibility
- S3 bucket remains private (Block Public Access enabled)
- Origin Access Control (OAC) for secure S3 access
- Small payloads (≤100KB) for fast delivery

## CORS Configuration

### CloudFront CORS Headers

CloudFront automatically adds CORS headers via Response Headers Policy:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, HEAD, OPTIONS`
- `Access-Control-Allow-Headers: *`
- `Access-Control-Max-Age: 3600`
- `Cache-Control: public, max-age=3600`

### S3 Bucket CORS

The S3 bucket also has CORS configuration as a fallback:

```json
{
  "allowed_headers": ["*"],
  "allowed_methods": ["GET", "HEAD"],
  "allowed_origins": ["*"],
  "expose_headers": ["ETag", "Content-Length", "Content-Type"],
  "max_age_seconds": 3600
}
```

## Security Model

### Public Access Scope

**✅ Publicly Accessible:**
- Gold bucket `served/` prefix only (via CloudFront)
- Read-only access (GET and HEAD)
- All JSON artifacts under `served/`

**🔒 Private (No Public Access):**
- Bronze bucket (all objects)
- Silver bucket (all objects)
- Gold bucket - direct S3 access blocked
- Gold bucket root and other prefixes
- Gold bucket internal Parquet files
- Access logs bucket

### Security Measures

1. **CloudFront OAC:** Uses Origin Access Control with signed requests to access S3
2. **Bucket Policy:** Explicitly grants access only to CloudFront service principal with matching distribution ARN
3. **Resource Restriction:** Bucket policy limits access to `served/*` pattern only
4. **Public Access Block:** All settings enabled (block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets)
5. **HTTPS Only:** CloudFront enforces HTTPS via redirect-to-https viewer protocol policy
6. **CORS Restrictions:** Only GET, HEAD, and OPTIONS methods allowed (no write operations)
7. **Encryption:** AES256 server-side encryption on all S3 objects
8. **Versioning:** Enabled for audit trail and recovery
9. **Access Logging:** All S3 requests logged to access logs bucket

### IAM Permissions

**CloudFront (via OAC):**
- `s3:GetObject` on `hoopstat-haus-gold/served/*`
- Authenticated via service principal with source ARN condition

**Public Users (Anonymous):**
- No direct S3 access
- Access only via CloudFront distribution

## Performance Characteristics

### Expected Latency

- **CloudFront edge (cache hit):** 10-50ms (from nearest edge location)
- **CloudFront to S3 (cache miss):** 100-300ms (first request or after cache expiration)
- **Cache TTL:** Default 1 hour, max 24 hours
- Small payloads (≤100KB) ensure fast delivery over any connection

### Caching Behavior

- **Cache key:** URL path only (no query strings)
- **Compression:** Automatic gzip/brotli compression enabled
- **Default TTL:** 3600 seconds (1 hour)
- **Max TTL:** 86400 seconds (24 hours)
- **Min TTL:** 0 seconds (immediate revalidation if needed)

## Testing Public Access

### Get CloudFront Domain

First, retrieve the CloudFront domain from Terraform outputs:

```bash
cd infrastructure
terraform output cloudfront_distribution
```

### Verify CloudFront Access

```bash
# Replace <cloudfront-domain> with actual domain from Terraform output
curl -i https://<cloudfront-domain>.cloudfront.net/index/latest.json

# Expected response headers:
# HTTP/2 200 OK
# Content-Type: application/json
# Access-Control-Allow-Origin: *
# X-Cache: Hit from cloudfront (or Miss from cloudfront)
# Cache-Control: public, max-age=3600
```

### Verify CORS from Browser

```javascript
// Browser JavaScript test
// Replace <cloudfront-domain> with actual domain
fetch('https://<cloudfront-domain>.cloudfront.net/index/latest.json')
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

### Verify Direct S3 Access is Blocked

```bash
# Attempt direct S3 access (should fail with 403)
curl -i https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/index/latest.json
# Expected: 403 Forbidden (Access Denied)

# Attempt to access non-served prefix via CloudFront (should fail with 403)
curl -i https://<cloudfront-domain>.cloudfront.net/../internal/data.parquet
# Expected: 403 Forbidden or 404 Not Found
```

### Verify Cache Behavior

```bash
# First request (cache miss)
curl -i https://<cloudfront-domain>.cloudfront.net/index/latest.json | grep X-Cache
# Expected: X-Cache: Miss from cloudfront

# Second request (cache hit)
curl -i https://<cloudfront-domain>.cloudfront.net/index/latest.json | grep X-Cache
# Expected: X-Cache: Hit from cloudfront
```

## Monitoring

### CloudFront Metrics

Available in CloudFront console and CloudWatch:
- Requests (total, per edge location)
- Bytes downloaded/uploaded
- 4xx/5xx error rates
- Cache hit ratio
- Origin latency

### S3 Metrics

Available in S3 console:
- GET requests to `served/` prefix (from CloudFront origin)
- 4xx/5xx errors
- Bytes downloaded
- First byte latency

### Access Logs

S3 access logs are stored in `hoopstat-haus-access-logs` bucket:
- Prefix: `gold/`
- Retention: 90 days
- Format: S3 server access log format
- Note: Only CloudFront origin requests are logged (not end-user requests)

## Troubleshooting

### CORS Errors in Browser

**Symptom:** Browser console shows CORS error

**Solutions:**
1. Check that artifact exists (404 won't trigger CORS properly)
2. Verify using CloudFront URL (not direct S3 URL)
3. Verify response headers include `Access-Control-Allow-Origin`
4. Ensure you're using HTTPS (not HTTP)
5. Check CloudFront distribution status is "Deployed"

### 403 Forbidden Errors

**Symptom:** HTTP 403 when accessing artifacts

**Possible Causes:**
1. Using direct S3 URL instead of CloudFront URL
2. Accessing wrong prefix (not under `served/`)
3. CloudFront distribution not fully deployed
4. Bucket policy not applied (check Terraform apply)

**Solutions:**
1. Use CloudFront URL from Terraform outputs
2. Verify URL path structure (no `/served/` needed in CloudFront URL)
3. Wait for CloudFront distribution to reach "Deployed" status
4. Run `terraform plan` to verify configuration matches
5. Check bucket policy in S3 console

### Cache Issues

**Symptom:** Stale content served or updates not visible

**Solutions:**
1. Wait for TTL to expire (default 1 hour)
2. Create CloudFront invalidation for specific paths
3. Check X-Cache header to verify cache behavior
4. For testing, use unique query strings to bypass cache

## Cost Optimization

### Expected Costs

**CloudFront:**
- Data transfer out to internet: $0.085 per GB (first 10TB, US/Europe)
- HTTPS requests: $0.0100 per 10,000 requests
- No charge for data transfer from S3 to CloudFront

**S3:**
- Storage: $0.023 per GB-month (Standard)
- GET requests from CloudFront: $0.0004 per 1,000 requests
- No data transfer charges for CloudFront origin fetches

**Estimated Monthly Cost (assuming 1M requests, 100KB avg, 50% cache hit ratio):**
- CloudFront HTTPS requests (1M): $1.00
- CloudFront data transfer (100GB): $8.50
- S3 storage (10GB): $0.23
- S3 GET requests (500K cache misses): $0.20
- **Total: ~$9.93/month**

**Comparison to Direct S3:**
- Direct S3 would cost ~$9.40/month (saves ~$0.53/month)
- CloudFront adds minimal cost but provides:
  - Better performance (edge caching)
  - Private S3 bucket (security compliance)
  - Built-in DDoS protection
  - HTTPS certificate management

### Cost Reduction Tips

1. Keep artifacts under 100KB size limit for faster delivery
2. Monitor CloudFront cache hit ratio (aim for >80%)
3. Use efficient JSON serialization to minimize file sizes
4. Consider cache invalidation costs when updating artifacts
5. Review CloudFront price class if traffic is regional

## Publishing Artifacts

### Upload to S3

Artifacts are uploaded to the Gold bucket's `served/` prefix using AWS CLI or SDK:

```bash
# Using AWS CLI
aws s3 cp local-file.json s3://hoopstat-haus-gold/served/path/to/file.json

# Using AWS SDK (Python boto3 example)
import boto3
s3 = boto3.client('s3')
s3.upload_file('local-file.json', 'hoopstat-haus-gold', 'served/path/to/file.json')
```

### Cache Invalidation (Optional)

After uploading new artifacts, you can invalidate the CloudFront cache to serve updated content immediately:

```bash
# Invalidate specific path
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/path/to/file.json"

# Invalidate all artifacts (use sparingly - costs apply)
aws cloudfront create-invalidation \
  --distribution-id <distribution-id> \
  --paths "/*"
```

**Note:** Cache invalidations are free for the first 1,000 paths per month. Additional paths cost $0.005 per path.

### Automated Publishing

For automated workflows (e.g., GitHub Actions), ensure the IAM role has:
- `s3:PutObject` permission on `hoopstat-haus-gold/served/*`
- (Optional) `cloudfront:CreateInvalidation` for cache invalidation

## References

- [ADR-028: Gold Layer Architecture](../meta/adr/ADR-028-gold_layer_final.md)
- [JSON Artifact Schemas](../docs-src/JSON_ARTIFACT_SCHEMAS.md)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [AWS CloudFront OAC Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
