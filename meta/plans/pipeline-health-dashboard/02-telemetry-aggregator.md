# Ticket 2: Build Telemetry Aggregator Lambda

**Title:** `feat: Build telemetry aggregator Lambda for pipeline health JSON`

**Labels:** `enhancement`

---

## What do you want to build?

Build a Python Lambda function that aggregates pipeline execution telemetry from CloudWatch Logs and S3 quarantine data, then compiles the results into a `pipeline_health.json` artifact conforming to the schema defined in Ticket 1.

This aggregator is the core backend component of the health dashboard. It runs once daily after Gold processing completes and produces a single static JSON file that the dashboard UI consumes.

### Data Sources

The aggregator queries three data sources, all read-only:

1. **CloudWatch Logs Insights** — Query the `/hoopstat-haus/data-pipeline` log group for pipeline execution outcomes across the last 7 days. The logs use structured JSON format (per ADR-015), so the aggregator can filter on fields like `status`, `stage`, and `timestamp`.

2. **S3 Quarantine Prefix** — Count quarantine files under `s3://hoopstat-haus-bronze/quarantine/year=YYYY/month=MM/day=DD/` for each of the last 7 days to determine daily quarantine volumes.

3. **S3 Gold Artifacts** — Check for the existence and last-modified timestamp of `served/index/latest.json` in the Gold bucket to confirm Gold layer completion.

### Processing Logic

```
1. Query CloudWatch Logs Insights for Bronze/Silver/Gold execution status (last 7 days)
2. List quarantine files per day from S3 (last 7 days)
3. Check Gold latest.json last-modified timestamp
4. Compile daily summaries array
5. Derive stage statuses and overall system status
6. Validate output against Pydantic schema (Ticket 1)
7. Sanitize output (Ticket 3 — placeholder: basic validation here)
8. Write pipeline_health.json to s3://hoopstat-haus-gold/served/health/pipeline_health.json
```

### Application Structure

Create a new app under `apps/health-aggregator/` following existing app patterns:

```
apps/health-aggregator/
├── app/
│   ├── __init__.py
│   ├── main.py           # Lambda handler entry point
│   ├── aggregator.py     # Core aggregation logic
│   ├── cloudwatch.py     # CloudWatch Logs Insights queries
│   ├── s3_reader.py      # S3 quarantine and artifact checks
│   └── writer.py         # Write pipeline_health.json to S3
├── tests/
│   ├── __init__.py
│   ├── test_aggregator.py
│   ├── test_cloudwatch.py
│   ├── test_s3_reader.py
│   └── test_writer.py
├── pyproject.toml
├── poetry.lock
├── Dockerfile
└── README.md
```

---

## Acceptance Criteria

- [ ] A new `apps/health-aggregator/` app is created with Poetry project structure
- [ ] The Lambda handler queries CloudWatch Logs Insights for the last 7 days of pipeline execution data
- [ ] The Lambda reads quarantine file counts from the Bronze S3 bucket for the last 7 days
- [ ] The Lambda checks Gold layer completion via the `latest.json` artifact timestamp
- [ ] Output is validated against the Pydantic models from Ticket 1 before writing
- [ ] The compiled `pipeline_health.json` is written to `s3://hoopstat-haus-gold/served/health/pipeline_health.json` with `Cache-Control: public, max-age=3600`
- [ ] The aggregator handles missing data gracefully (e.g., no quarantine files for a given day → `records_quarantined: 0`)
- [ ] The aggregator handles CloudWatch query failures gracefully (logs the error, writes a degraded status JSON rather than failing silently)
- [ ] Unit tests achieve ≥90% coverage of the aggregation logic using mocked AWS clients (boto3 stubs or moto)
- [ ] The app passes `poetry run ruff format --check .` and `poetry run ruff check .`

---

## Implementation Notes (Optional)

- Follow the existing app structure patterns from `apps/gold-analytics/` and `apps/silver-processing/` for Poetry config, Dockerfile, and logging setup.
- Use `boto3` for CloudWatch Logs Insights (`start_query` / `get_query_results`) and S3 (`list_objects_v2`, `head_object`, `put_object`).
- The Lambda shares the same CloudWatch log group (`/hoopstat-haus/data-pipeline`) as the existing pipeline Lambdas per ADR-018.
- The S3 `Cache-Control` header follows the same pattern as the frontend assets (1-hour TTL) per ADR-038.
- Use structured JSON logging per ADR-015 for the aggregator's own operational logs.
- **Dependency on Ticket 1:** The Pydantic models must be available in `hoopstat-data` before this ticket can be completed.
- **Sanitization:** Basic output validation is included here, but the comprehensive sanitization logic is in Ticket 3. This ticket should include a placeholder sanitization step that Ticket 3 will replace with the full implementation.
