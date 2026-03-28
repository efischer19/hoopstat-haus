# Health Dashboard Operational Runbook

Operational guide for the pipeline health dashboard system. Covers manual debugging, output interpretation, troubleshooting, and cache verification.

For architecture context, see [ADR-040 — Static Pipeline Health Dashboard](../meta/adr/ADR-040-static-pipeline-health-dashboard.md).

## Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Health Aggregator Lambda | `apps/health-aggregator/` | Collects telemetry, produces `pipeline_health.json` |
| Health Models | `libs/hoopstat-data/hoopstat_data/health_models.py` | Pydantic schema for the JSON artifact |
| Dashboard UI | `frontend-app/health.html` | Static HTML page that renders the JSON |
| Dashboard JS | `frontend-app/scripts/health.js` | Fetches and renders health data |

## Manually Triggering the Aggregator

### Via AWS CLI

Invoke the Lambda directly for debugging:

```bash
aws lambda invoke \
  --function-name hoopstat-haus-health-aggregator \
  --payload '{}' \
  --region us-east-1 \
  /tmp/health-response.json

cat /tmp/health-response.json
```

The response includes a top-level `statusCode` and a `body` field; the `body` JSON contains `overall_status`, `generated_at`, and `message`.

### Via Local Execution

Run the aggregation pipeline locally against real AWS resources (requires valid AWS credentials):

```bash
cd apps/health-aggregator
export BRONZE_BUCKET=hoopstat-haus-bronze
export GOLD_BUCKET=hoopstat-haus-gold
export AWS_REGION=us-east-1

poetry run python -c "
from app.main import lambda_handler
result = lambda_handler({}, None)
print(result)
"
```

### Via Integration Tests

Run the mocked integration tests to verify the pipeline logic without AWS access:

```bash
cd apps/health-aggregator
poetry run pytest tests/integration/ -v
```

## Interpreting `pipeline_health.json`

### Schema Overview

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-03-28T06:00:00Z",
  "overall_status": "operational",
  "stages": {
    "bronze": { "status": "operational", "last_success_at": "2026-03-28T00:00:00Z" },
    "silver": { "status": "operational", "last_success_at": "2026-03-28T00:00:00Z" },
    "gold":   { "status": "operational", "last_success_at": "2026-03-28T06:00:00Z" }
  },
  "daily_summaries": [
    {
      "date": "2026-03-28",
      "bronze": { "status": "success", "records_ingested": 100 },
      "silver": { "status": "success", "records_processed": 95, "records_quarantined": 5, "quality_score": 0.95 },
      "gold":   { "status": "success", "artifacts_written": 10 }
    }
  ]
}
```

### Status Values

| Field | Possible Values | Meaning |
|-------|----------------|---------|
| `overall_status` | `operational` | All stages healthy |
| | `degraded` | One or more stages have issues |
| | `outage` | Critical failure; one or more stages completely down |
| `stages.*.status` | `operational` / `degraded` / `outage` | Per-stage health roll-up |
| `daily_summaries.*.{stage}.status` | `success` / `failed` / `skipped` / `no_data` | Individual run outcome |

### Key Metrics

- **`records_ingested`** — Number of records pulled from the NBA API during Bronze ingestion
- **`records_processed`** — Number of records successfully transformed during Silver processing
- **`records_quarantined`** — Number of records that failed validation and were quarantined (sourced from S3 quarantine prefix, not CloudWatch)
- **`quality_score`** — Ratio of processed to total records: `processed / (processed + quarantined)`. A score of 1.0 means zero quarantines; below 0.8 indicates significant data quality issues.
- **`artifacts_written`** — Number of Gold JSON artifacts produced

### Status Derivation Rules

1. **Stage status** is derived from the most recent daily run:
   - Most recent = `success` → stage is `operational`
   - Most recent = `failed` → stage is `degraded`
   - Most recent = `no_data` or `skipped` with no successes in window → stage is `outage`

2. **Overall status** is the worst of all stage statuses:
   - Any stage `outage` → overall `outage`
   - Any stage `degraded` → overall `degraded`
   - All stages `operational` → overall `operational`

## Troubleshooting: Sanitizer Payload Rejection

When the sanitizer rejects a payload, the following happens:

1. A warning is logged to CloudWatch: `"Sensitive pattern detected in serialized health report payload"`
2. The entire payload is replaced with a minimal fallback report (`overall_status: degraded`, empty stages and summaries)
3. The fallback report is written to S3 instead of the original

### How to Investigate

1. **Check CloudWatch Logs** for the health-aggregator Lambda. Look for:
   - `"Sensitive pattern detected"` — identifies which regex pattern matched
   - `"Payload rejected by security filter"` — confirms rejection occurred

2. **Check the upstream pipeline logs** (Bronze, Silver, Gold) for the same time window. The sensitive data likely originated from a log message that CloudWatch Logs Insights returned.

3. **Review the secret patterns** in `apps/health-aggregator/app/sanitizer.py` (`_SECRET_PATTERNS` list). Common triggers:
   - AWS access key IDs (`AKIA...`)
   - AWS ARNs (`arn:aws:...`)
   - Internal IPs (RFC 1918: `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`)
   - Bearer tokens
   - API key patterns

4. **Re-run locally** with the same input data to reproduce:

```bash
cd apps/health-aggregator
poetry run python -c "
from app.aggregator import HealthAggregator
from unittest.mock import MagicMock

# Reproduce with mock data matching the problematic CW query results
cw_mock = MagicMock()
cw_mock.query_pipeline_status.return_value = [...]  # paste CW rows here
s3_mock = MagicMock()
s3_mock.count_quarantine_files.return_value = 0
s3_mock.get_gold_index_last_modified.return_value = None

aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_mock)
report = aggregator.aggregate()
print(report.overall_status)
"
```

### Resolution

The sanitizer's allowlist reconstruction (Pass 1) should prevent sensitive data from reaching the output. If Pass 2 (secret scan) is triggering, it means Pass 1 has a gap. File a bug to add the missing field to the allowlist in `_reconstruct_allowlisted_dict()`.

## Verifying CloudFront Cache

### Check Current Cached Version

```bash
# Fetch the artifact directly from CloudFront
curl -s https://YOUR_CLOUDFRONT_DOMAIN/health/pipeline_health.json | jq '.generated_at, .overall_status'

# Check cache headers
curl -sI https://YOUR_CLOUDFRONT_DOMAIN/health/pipeline_health.json | grep -i 'cache-control\|x-cache\|age'
```

Expected headers:
- `Cache-Control: public, max-age=3600` — 1-hour TTL
- `X-Cache: Hit from cloudfront` — served from edge cache
- `Age: <seconds>` — time since last origin fetch

### Force Cache Invalidation

If the cached version is stale or incorrect:

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/health/pipeline_health.json"
```

### Verify Origin (S3)

Check the artifact directly in S3 (bypassing CloudFront):

```bash
aws s3 cp s3://hoopstat-haus-gold/served/health/pipeline_health.json - | jq .
```

Compare `generated_at` between S3 and CloudFront to confirm cache freshness.
