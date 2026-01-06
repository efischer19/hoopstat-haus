# Public Access Guide for JSON Artifacts

**Status:** Production  
**Last Updated:** 2026-01-06  
**Related ADRs:** [ADR-028](../meta/adr/ADR-028-gold_layer_final.md)

## Overview

This guide documents the public access configuration for JSON artifacts served from the Gold layer S3 bucket. The infrastructure enables direct browser access to pre-computed basketball analytics with proper security and CORS headers.

## Architecture

```
Browser/App
    ↓
S3 Gold Bucket (served/ prefix only)
    └── served/
        ├── player_daily/{date}/{player_id}.json
        ├── team_daily/{date}/{team_id}.json
        ├── top_lists/{date}/{metric}.json
        └── index/latest.json
```

## Access Method

### Direct S3 Access

**Base URL:** `https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served`

**Example URLs:**
```
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/player_daily/2024-11-15/2544.json
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/team_daily/2024-11-15/1610612747.json
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/top_lists/2024-11-15/top_scorers.json
https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/index/latest.json
```

**Features:**
- Direct HTTPS access to S3 bucket
- CORS enabled for browser compatibility
- Public read access to served/ prefix only
- Small payloads (≤100KB) for fast delivery

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
4. **Encryption:** AES256 server-side encryption on all S3 objects
5. **Versioning:** Enabled for audit trail and recovery
6. **Access Logging:** All S3 requests logged to access logs bucket

### IAM Permissions

**Public Users (Anonymous):**
- `s3:GetObject` on `hoopstat-haus-gold/served/*`
- `s3:GetObjectVersion` on `hoopstat-haus-gold/served/*`

## Performance Characteristics

### Expected Latency

- **S3 direct access:** 100-200ms (varies by region and network)
- Small payloads (≤100KB) ensure fast delivery over any connection

## Testing Public Access

### Verify S3 Access

```bash
# Get artifact directly from S3
curl -i https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/index/latest.json

# Expected response headers:
# HTTP/1.1 200 OK
# Content-Type: application/json
# Access-Control-Allow-Origin: *
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
fetch('https://hoopstat-haus-gold.s3.us-east-1.amazonaws.com/served/index/latest.json')
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

## Monitoring

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
1. Check that artifact exists (404 won't trigger CORS properly)
2. Verify S3 CORS configuration is applied
3. Verify response headers include `Access-Control-Allow-Origin`
4. Ensure you're using HTTPS (not HTTP)

### 403 Forbidden Errors

**Symptom:** HTTP 403 when accessing artifacts

**Possible Causes:**
1. Accessing wrong prefix (not under `served/`)
2. Bucket policy not applied (check Terraform apply)
3. Public access block settings incorrect

**Solutions:**
1. Verify URL path includes `/served/` prefix
2. Run `terraform plan` to verify configuration matches
3. Check bucket policy in S3 console

## Cost Optimization

### Expected Costs

**S3:**
- Storage: $0.023 per GB-month (Standard)
- GET requests: $0.0004 per 1,000 requests
- Data transfer out to internet: $0.09 per GB (first 10TB)

**Estimated Monthly Cost (assuming 1M requests, 100KB avg):**
- S3 storage (10GB): $0.23
- S3 GET requests: $0.40
- S3 data transfer (100GB): $9.00
- **Total: ~$9.63/month**

### Cost Reduction Tips

1. Keep artifacts under 100KB size limit for faster delivery
2. Monitor S3 request metrics to optimize access patterns
3. Use efficient JSON serialization to minimize file sizes
4. Consider data transfer costs when estimating usage

## References

- [ADR-028: Gold Layer Architecture](../meta/adr/ADR-028-gold_layer_final.md)
- [JSON Artifact Schemas](../docs-src/JSON_ARTIFACT_SCHEMAS.md)
- [AWS S3 CORS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)
