# health-aggregator

Telemetry aggregator Lambda that compiles `pipeline_health.json` for the static pipeline health dashboard per [ADR-040](../../meta/adr/ADR-040-static-pipeline-health-dashboard.md).

## Overview

This Lambda runs once daily (EventBridge schedule) after Gold processing completes. It:

1. Queries CloudWatch Logs Insights (`/hoopstat-haus/data-pipeline`) for the last 7 days of Bronze / Silver / Gold execution statuses.
2. Counts quarantine files from the Bronze S3 bucket (`quarantine/year=YYYY/month=MM/day=DD/`).
3. Checks the Gold `served/index/latest.json` last-modified timestamp to confirm Gold layer completion.
4. Compiles and validates a `PipelineHealthReport` (Pydantic schema from `hoopstat-data`).
5. Sanitizes the output via a two-pass security layer (see [Security Model](#security-model) below).
6. Writes `pipeline_health.json` to `s3://hoopstat-haus-gold/served/health/pipeline_health.json` with `Cache-Control: public, max-age=3600`.

On CloudWatch query failure, a degraded-status report (OUTAGE across all stages) is written rather than leaving the artifact stale.

## Architecture Decision Record

This application implements the **Static Generation Pattern** described in [ADR-040 — Static Pipeline Health Dashboard](../../meta/adr/ADR-040-static-pipeline-health-dashboard.md). The ADR covers:

- Why a static JSON artifact was chosen over a live API
- The two-pass sanitization security model
- CDN caching strategy (1-hour TTL via CloudFront)
- Cost protection and graceful degradation requirements

## Environment Variables

| Variable        | Description                              |
|-----------------|------------------------------------------|
| `BRONZE_BUCKET` | S3 bucket name for the Bronze layer      |
| `GOLD_BUCKET`   | S3 bucket name for the Gold layer        |
| `AWS_REGION`    | AWS region (default: `us-east-1`)        |

## Development

### Setup

```bash
# Install dependencies
poetry install

# Format
poetry run ruff format .

# Lint
poetry run ruff check .
```

### Running Tests

```bash
# Run all tests (unit + integration)
poetry run pytest --cov=app --cov-report=term-missing

# Run only unit tests
poetry run pytest tests/test_*.py -v

# Run only integration tests
poetry run pytest tests/integration/ -v
```

Alternatively, use the repository's CI check script from the repo root:

```bash
./scripts/local-ci-check.sh apps/health-aggregator
```

### Integration Tests

The `tests/integration/` directory contains end-to-end integration tests that validate the complete aggregation pipeline using moto-mocked AWS services. Five scenarios are covered:

| Scenario | Description | Key Assertions |
|----------|-------------|----------------|
| 1. Happy Path | All stages succeed for 7 days | `overall_status: operational`, correct record counts, valid S3 artifact |
| 2. Bronze Failure | Bronze ingestion fails, no Silver/Gold data | `overall_status: outage`, Bronze degraded, Silver/Gold outage |
| 3. Silver Quarantine | High quarantine counts during Silver processing | Accurate quarantine counts, quality score reflects ratio |
| 4. Security | Secret patterns injected into mock data | Sanitizer rejects payload, fallback JSON contains no secrets |
| 5. Resilience | CloudWatch query timeout/failure | Degraded OUTAGE report written, all stages NO_DATA |

## Security Model

The sanitizer (`app/sanitizer.py`) implements the [ADR-040 §Security Model](../../meta/adr/ADR-040-static-pipeline-health-dashboard.md) with two passes:

1. **Pass 1 — Field-level allowlist reconstruction:** Builds a new output dict from scratch using only validated, explicitly permitted fields. Values outside permitted ranges are clamped/defaulted. Any field not on the allowlist is silently discarded.

2. **Pass 2 — Secret-detection scan:** Serialises the reconstructed dict to JSON and scans for patterns matching AWS credentials, ARNs, internal IPs, Bearer tokens, and API keys. If any pattern matches, the entire payload is replaced with a minimal safe fallback.

## Application Structure

```
app/
├── __init__.py        # Package init
├── main.py            # Lambda handler entry point
├── aggregator.py      # Core aggregation logic
├── cloudwatch.py      # CloudWatch Logs Insights queries
├── s3_reader.py       # S3 quarantine and artifact checks
├── sanitizer.py       # Two-pass sanitization (ADR-040 §Security Model)
└── writer.py          # Write pipeline_health.json to S3
tests/
├── __init__.py
├── test_aggregator.py     # Unit tests for aggregation logic
├── test_cloudwatch.py     # Unit tests for CloudWatch client
├── test_main.py           # Unit tests for Lambda handler
├── test_s3_reader.py      # Unit tests for S3 reader
├── test_sanitizer.py      # Security-focused unit tests
├── test_writer.py         # Unit tests for S3 writer
└── integration/
    ├── __init__.py
    └── test_end_to_end.py # End-to-end integration tests (5 scenarios)
```

## Docker Build

The build context must be the repository root so Poetry can resolve local path dependencies:

```bash
docker build -f apps/health-aggregator/Dockerfile -t health-aggregator:dev .
```
