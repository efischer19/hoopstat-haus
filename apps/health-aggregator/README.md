# health-aggregator

Telemetry aggregator Lambda that compiles `pipeline_health.json` for the static pipeline health dashboard per [ADR-040](../../meta/adr/ADR-040-static-pipeline-health-dashboard.md).

## Overview

This Lambda runs once daily (EventBridge schedule) after Gold processing completes. It:

1. Queries CloudWatch Logs Insights (`/hoopstat-haus/data-pipeline`) for the last 7 days of Bronze / Silver / Gold execution statuses.
2. Counts quarantine files from the Bronze S3 bucket (`quarantine/year=YYYY/month=MM/day=DD/`).
3. Checks the Gold `served/index/latest.json` last-modified timestamp to confirm Gold layer completion.
4. Compiles and validates a `PipelineHealthReport` (Pydantic schema from `hoopstat-data`).
5. Sanitizes the output to strip any sensitive data (AWS ARNs, access keys, etc.).
6. Writes `pipeline_health.json` to `s3://hoopstat-haus-gold/served/health/pipeline_health.json` with `Cache-Control: public, max-age=3600`.

On CloudWatch query failure, a degraded-status report (OUTAGE across all stages) is written rather than leaving the artifact stale.

## Environment Variables

| Variable        | Description                              |
|-----------------|------------------------------------------|
| `BRONZE_BUCKET` | S3 bucket name for the Bronze layer      |
| `GOLD_BUCKET`   | S3 bucket name for the Gold layer        |
| `AWS_REGION`    | AWS region (default: `us-east-1`)        |

## Development

```bash
# Install dependencies
poetry install

# Format
poetry run ruff format .

# Lint
poetry run ruff check .

# Test with coverage
poetry run pytest --cov=app --cov-report=term-missing
```

## Application Structure

```
app/
├── __init__.py        # Package init
├── main.py            # Lambda handler entry point
├── aggregator.py      # Core aggregation logic + sanitization
├── cloudwatch.py      # CloudWatch Logs Insights queries
├── s3_reader.py       # S3 quarantine and artifact checks
└── writer.py          # Write pipeline_health.json to S3
tests/
├── __init__.py
├── test_aggregator.py
├── test_cloudwatch.py
├── test_s3_reader.py
└── test_writer.py
```

## Docker Build

The build context must be the repository root so Poetry can resolve local path dependencies:

```bash
docker build -f apps/health-aggregator/Dockerfile -t health-aggregator:dev .
```
