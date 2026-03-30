# feat: Migrate data pipeline apps and shared libraries to hoopstat-data

## What do you want to build?

Migrate the core data pipeline applications and shared libraries from hoopstat-haus to hoopstat-data. This is the largest migration ticket and involves careful consideration of what to copy vs. rewrite.

## Acceptance Criteria

- [ ] All data pipeline apps are present in `hoopstat-data/apps/`:
  - `bronze-ingestion/`
  - `silver-processing/`
  - `gold-analytics/`
  - `db-compiler/`
  - `health-aggregator/`
  - `mcp-local-proxy/`
- [ ] All shared libraries are present in `hoopstat-data/libs/`:
  - `hoopstat-config/`
  - `hoopstat-data/` (the data models library)
  - `hoopstat-observability/`
  - `hoopstat-nba_api/`
  - `hoopstat-s3/`
  - `hoopstat-mock-data/`
  - `hoopstat-e2e-testing/`
- [ ] All `pyproject.toml` files have correct path dependencies for the new repo structure
- [ ] All `poetry.lock` files are regenerated
- [ ] `poetry install` succeeds in every app and lib directory
- [ ] `poetry run ruff format --check .` passes in every app and lib
- [ ] `poetry run ruff check .` passes in every app and lib
- [ ] `poetry run pytest` passes in every app and lib
- [ ] Relevant documentation is migrated: `docs-src/`, `mkdocs.yml`, `docs-requirements.txt`
- [ ] Utility scripts are migrated: `scripts/` (relevant ones per file mapping)
- [ ] Project-specific ADRs are migrated to `meta/adr/` (per file mapping document)
- [ ] `templates/python-app-template/` and `templates/python-lib-template/` are present

## Implementation Notes (Optional)

This is a **copy, not rewrite** operation for most content. The code has been proven in hoopstat-haus and should be brought over intact. The main changes needed are path adjustments.

Migration approach:
1. Copy each `apps/` directory as-is
2. Copy each `libs/` directory as-is
3. Update path dependencies in `pyproject.toml` files (these should be the same relative paths, so minimal changes expected)
4. Regenerate `poetry.lock` files
5. Copy relevant scripts from `scripts/`
6. Copy relevant ADRs from `meta/adr/`
7. Run the full quality check suite

For ADR migration, refer to the file-mapping document (ticket 01). General rules:
- Technology choice ADRs (Python, Poetry, pytest, Ruff, Docker, AWS, Terraform, etc.) are already in the blueprint templates
- Data-specific ADRs (medallion architecture, S3 key naming, JSON artifacts, etc.) belong in hoopstat-data
- The original ADR numbers should be preserved for traceability

Watch out for:
- The `mcp-local-proxy` app has a TypeScript component — ensure that's included
- `hoopstat-e2e-testing` uses LocalStack — verify that works in the new repo context
- `db-compiler` has schema files under `apps/db-compiler/schema/` — don't forget these
- Documentation scripts that reference specific file paths may need updating
