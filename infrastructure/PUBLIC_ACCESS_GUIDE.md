# Public Access Guide for JSON Artifacts

**Status:** Production  
**Last Updated:** 2026-01-06  
**Related ADRs:** [ADR-028](../meta/adr/ADR-028-gold_layer_final.md)

## Overview

This guide documents the public access configuration for JSON artifacts served from the Gold layer S3 bucket. The infrastructure enables direct browser access to pre-computed basketball analytics with proper security, CORS headers, and CDN caching.

## Architecture

```
Browser/App
    ↓
CloudFront Distribution (Recommended)
    ↓
S3 Gold Bucket (served/ prefix only)
    └── served/
        ├── player_daily/{date}/{player_id}.json
        ├── team_daily/{date}/{team_id}.json
        ├── top_lists/{date}/{metric}.json
        └── index/latest.json
```

## Access Methods

### 1. CloudFront CDN (Recommended)

**Base URL:** `https://{cloudfront-domain-name}`

**Example URLs:**
```
https://{cloudfront-domain}/player_daily/2024-11-15/2544.json
https://{cloudfront-domain}/team_daily/2024-11-15/1610612747.json
https://{cloudfront-domain}/top_lists/2024-11-15/top_scorers.json
https://{cloudfront-domain}/index/latest.json
```

**Benefits:**
- Global edge caching for low latency
- Automatic HTTPS redirect
- Gzip/Brotli compression
- 1-hour default cache TTL
- 24-hour maximum cache TTL
- CORS headers automatically included

**Configuration:**
- Price Class: PriceClass_100 (North America and Europe)
- Origin: S3 Gold bucket with `/served` prefix
- Origin Access Control (OAC) for secure S3 access
- Response headers policy for CORS

### 2. Direct S3 Access

**Base URL:** `https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served`

**Example URLs:**
```
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/player_daily/2024-11-15/2544.json
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/team_daily/2024-11-15/1610612747.json
```

**Use Cases:**
- Debugging and testing
- Bypassing CDN cache during development
- Direct verification of S3 content

**Note:** CloudFront is recommended for production use due to better performance and caching.

## CORS Configuration

### S3 Bucket CORS

```json
{
  "allowed_headers": ["*"],
  "allowed_methods": ["GET", "HEAD"],
  "allowed_origins": ["*"],
  "expose_headers": ["ETag", "Content-Length", "Content-Type"],
  "max_age_seconds": 3600
}
```

### CloudFront CORS Headers

Automatically added via response headers policy:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, HEAD, OPTIONS`
- `Access-Control-Allow-Headers: *`
- `Access-Control-Max-Age: 3600`
- `Cache-Control: public, max-age=3600`

## Security Model

### Public Access Scope

**✅ Publicly Accessible:**
- Gold bucket `served/` prefix only
- Read-only access (GET and HEAD)
- All JSON artifacts under `served/`

**🔒 Private (No Public Access):**
- Bronze bucket (all objects)
- Silver bucket (all objects)
- Gold bucket root and other prefixes
- Gold bucket internal Parquet files
- Access logs bucket

### Security Measures

1. **Bucket Policy:** Explicitly scopes public read to `served/*` pattern only
2. **Public Access Block:** 
   - Blocks public ACLs on all buckets
   - Ignores public ACLs on all buckets
   - Allows bucket policy on Gold bucket only for `served/` prefix
3. **CORS Restrictions:** Only GET and HEAD methods allowed (no write operations)
4. **CloudFront OAC:** Secure origin access using AWS signatures
5. **Encryption:** AES256 server-side encryption on all S3 objects
6. **Versioning:** Enabled for audit trail and recovery
7. **Access Logging:** All S3 requests logged to access logs bucket

### IAM Permissions

**Public Users (Anonymous):**
- `s3:GetObject` on `hoopstat-haus-gold/served/*`
- `s3:GetObjectVersion` on `hoopstat-haus-gold/served/*`

**CloudFront Distribution:**
- `s3:GetObject` on `hoopstat-haus-gold/served/*` via OAC
- Condition: Source ARN must match distribution ARN

## Performance Characteristics

### CloudFront Caching

**Cache Behavior:**
- Default TTL: 3600 seconds (1 hour)
- Maximum TTL: 86400 seconds (24 hours)
- Minimum TTL: 0 seconds
- Compression: Enabled (gzip, Brotli)

**Cache Keys:**
- URL path only (no query strings)
- CORS headers forwarded for proper response

**Edge Locations:** North America and Europe (PriceClass_100)

### Expected Latency

- **First request (cache miss):** 100-300ms (S3 retrieval + edge)
- **Cached requests:** 10-50ms (edge cache hit)
- **S3 direct:** 100-200ms (varies by region)

## Testing Public Access

### Verify CloudFront Access

```bash
# Get artifact via CloudFront
curl -i https://{cloudfront-domain}/index/latest.json

# Expected response headers:
# HTTP/2 200
# Content-Type: application/json
# Access-Control-Allow-Origin: *
# Cache-Control: public, max-age=3600
# X-Cache: Hit from cloudfront (or Miss from cloudfront)
```

### Verify Direct S3 Access

```bash
# Get artifact directly from S3
curl -i https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/index/latest.json

# Expected response headers:
# HTTP/1.1 200 OK
# Content-Type: application/json
# Access-Control-Allow-Origin: *
```

### Verify CORS from Browser

```javascript
// Browser JavaScript test
fetch('https://{cloudfront-domain}/index/latest.json')
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

### Verify Access Restrictions

```bash
# Attempt to access non-served prefix (should fail with 403)
curl -i https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/internal/data.parquet
# Expected: 403 Forbidden

# Attempt to access Bronze bucket (should fail with 403)
curl -i https://hoopstat-haus-bronze.s3.us-east-1.amazonaws.com/anything.json
# Expected: 403 Forbidden
```

## Cache Invalidation

If you need to invalidate CloudFront cache for updated artifacts:

```bash
# Using AWS CLI
aws cloudfront create-invalidation \
  --distribution-id {distribution-id} \
  --paths "/player_daily/2024-11-15/*" "/index/*"
```

**Note:** Cache invalidations have a cost after the first 1,000 per month. Consider versioning artifacts or using unique paths instead.

## Monitoring

### CloudFront Metrics

Available in CloudFront console:
- Requests (total, per region)
- Bytes downloaded/uploaded
- Error rate (4xx, 5xx)
- Cache hit ratio

### S3 Metrics

Available in S3 console:
- GET requests to `served/` prefix
- 4xx/5xx errors
- Bytes downloaded
- First byte latency

### Access Logs

S3 access logs are stored in `hoopstat-haus-access-logs` bucket:
- Prefix: `gold/`
- Retention: 90 days
- Format: S3 server access log format

## Troubleshooting

### CORS Errors in Browser

**Symptom:** Browser console shows CORS error

**Solutions:**
1. Verify you're using CloudFront URL (not S3 direct)
2. Check that artifact exists (404 won't trigger CORS)
3. Ensure CloudFront distribution is deployed
4. Verify response headers include `Access-Control-Allow-Origin`

### 403 Forbidden Errors

**Symptom:** HTTP 403 when accessing artifacts

**Possible Causes:**
1. Accessing wrong prefix (not under `served/`)
2. CloudFront not yet deployed (check distribution status)
3. Bucket policy not applied (check Terraform apply)
4. Public access block settings incorrect

**Solutions:**
1. Verify URL path includes `/served/` prefix
2. Check CloudFront distribution status in AWS console
3. Run `terraform plan` to verify configuration matches
4. Check bucket policy in S3 console

### Cache Not Updating

**Symptom:** Old data returned after S3 update

**Solutions:**
1. Wait for cache TTL to expire (up to 1 hour)
2. Use CloudFront invalidation for immediate update
3. Consider using unique filenames/paths for new versions

## Cost Optimization

### Expected Costs

**CloudFront:**
- First 10 TB/month: $0.085 per GB (North America)
- Free tier: 1 TB data transfer out per month (first 12 months)

**S3:**
- Storage: $0.023 per GB-month (Standard)
- GET requests: $0.0004 per 1,000 requests
- Data transfer out to CloudFront: Free

**Estimated Monthly Cost (assuming 1M requests, 100KB avg):**
- S3 storage (10GB): $0.23
- S3 GET requests: $0.40
- CloudFront (100GB transfer): $8.50
- **Total: ~$9/month**

### Cost Reduction Tips

1. Use CloudFront (S3→CloudFront transfer is free)
2. Keep artifacts under 100KB size limit
3. Set appropriate cache TTLs
4. Use CloudFront invalidations sparingly
5. Monitor and optimize cache hit ratio

## References

- [ADR-028: Gold Layer Architecture](../meta/adr/ADR-028-gold_layer_final.md)
- [JSON Artifact Schemas](../docs-src/JSON_ARTIFACT_SCHEMAS.md)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [AWS S3 CORS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)
