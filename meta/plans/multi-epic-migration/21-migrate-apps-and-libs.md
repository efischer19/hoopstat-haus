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
- [ ] Relevant documentation is migrated to `docs-src/`: DATABASE_GUIDE.md, DATA_DICTIONARY.md, E2E_TESTING.md, ECR_IMAGE_MANAGEMENT.md, HEALTH_DASHBOARD_RUNBOOK.md, JSON_ARTIFACT_SCHEMAS.md, BUILD_ORCHESTRATION.md, libraries/
- [ ] `mkdocs.yml` and `docs-requirements.txt` are adapted for hoopstat-data
- [ ] Product-specific utility scripts are migrated: ecr-helper.sh, generate-data-dictionary.py, generate-db-schema-docs.py, generate-docs.py, test-health-dashboard.sh, test-orchestration.md, validate-orchestration.sh, scripts/tests/
- [ ] Product-specific ADRs are migrated to `meta/adr/`: ADR-012 through ADR-014, ADR-017 through ADR-018, ADR-020, ADR-024 through ADR-028, ADR-030 through ADR-035, ADR-037 through ADR-038, ADR-040, ADR-041
- [ ] Product-specific meta files are migrated: `meta/DATA_AVAILABILITY_POLICY.md`, `meta/GOLD_LAYER_ANALYTICS_STRATEGY.md`
- [ ] Product-specific plans are migrated: all `meta/plans/` documents except `multi-epic-migration/`
- [ ] `testing/` directory is migrated: Dockerfile.test (adapt paths), test_integration_pipeline.py, validate_e2e_framework.py
- [ ] `MCP_SETUP.md` is migrated
- [ ] `docker-compose.test.yml` is migrated and adapted for standalone repo context
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
