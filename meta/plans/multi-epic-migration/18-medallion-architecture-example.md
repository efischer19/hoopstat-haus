# feat: Medallion architecture example structure for python-aws-data-blueprint

## What do you want to build?

Add a medallion architecture (Bronze/Silver/Gold) example structure to the `python-aws-data-blueprint` template. This provides a data pipeline scaffolding that demonstrates the pattern without implementing actual data processing.

## Acceptance Criteria

- [ ] Example apps are organized to demonstrate the medallion pattern: `apps/example-ingestion/` (Bronze), `apps/example-processing/` (Silver), `apps/example-analytics/` (Gold)
- [ ] Each example app has a minimal `pyproject.toml`, `app/main.py`, `Dockerfile`, and `tests/` directory
- [ ] The `app/main.py` in each example app contains a commented-out skeleton showing the expected data flow (read from S3, transform, write to S3)
- [ ] An example shared library `libs/example-data/` exists with Pydantic model skeletons for data validation
- [ ] S3 key path conventions are documented (e.g., `bronze/{source}/{date}/`, `silver/{entity}/{date}/`, `gold/served/`)
- [ ] `infrastructure/main.tf` is updated to include S3 buckets for each medallion layer (or a single bucket with key prefixes)
- [ ] An ADR explaining the medallion architecture pattern is present (generalized from hoopstat-haus ADRs 025/026/027/028)
- [ ] A `docs-src/` page or README section explains the medallion architecture and how to customize it
- [ ] `.github/workflows/` include scheduled workflow stubs for each pipeline stage

## Implementation Notes (Optional)

This is where the hoopstat-haus data pipeline architecture gets generalized. The goal is to provide a pattern, not a working pipeline.

From hoopstat-haus, adapt:
- The Bronze/Silver/Gold app structure → Generalized example apps with placeholder logic
- `libs/hoopstat-data/` models → Generalized Pydantic model skeletons
- S3 key conventions → Documented but configurable
- Pipeline scheduling → Workflow stubs with cron expressions (commented out)

The example code should include comments like:
```python
# TODO: Replace with your data source
# response = requests.get("https://your-api.example.com/data")
# data = response.json()
```

Do NOT include actual NBA API calls, basketball-specific models, or any hoopstat business logic. The medallion pattern should be presented as a general data engineering best practice.

Consider whether the medallion architecture ADR should live in this template or be deferred to project-specific repos. Given that this template explicitly targets data projects, it makes sense to include a generalized version here.
