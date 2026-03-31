# File-to-Repository Mapping

This document maps every folder and file in the hoopstat-haus monorepo to its intended destination repository as part of the multi-repository migration. It serves as the foundational planning artifact that all subsequent migration work depends on.

## Destination Repositories

| Short Name | Repository | Description |
|---|---|---|
| **blueprint-repo-blueprints** | blueprint-repo-blueprints | Language-agnostic template content for bootstrapping any new repo |
| **static-js-app-blueprint** | static-js-app-blueprint | Frontend template content (vanilla HTML/CSS/JS) |
| **python-project-blueprint** | python-project-blueprint | Python monorepo template content (apps + libs structure) |
| **python-aws-data-blueprint** | python-aws-data-blueprint | Python + AWS data pipeline template content |
| **hoopstat-data** | hoopstat-data | Product-specific data pipeline content |
| **hoopstat-app** | hoopstat-app | Product-specific frontend content |
| **Discard** | — | Build artifacts, repo-specific config that doesn't migrate |

## Migration Actions

- **Copy as-is** — File moves to destination unchanged
- **Adapt/Generalize** — File moves but must be modified to remove product-specific details
- **Rewrite** — Concept carries over but file is written from scratch for the destination
- **Scaffold** — An empty or minimal placeholder version is created in the destination

---

## Root-Level Files

| File | Destination | Action | Rationale |
|---|---|---|---|
| `.dockerignore` | **python-project-blueprint** | Adapt | Generic Docker ignore rules; remove hoopstat-specific entries if any |
| `.gitignore` | **Multiple** | Adapt | Each repo needs its own `.gitignore`. Python repos share the Python portion; frontend repo gets JS-specific rules. Blueprint repos get generalized versions |
| `.pre-commit-config.yaml` | **python-project-blueprint** | Copy as-is | Pre-commit hooks for ruff formatting/linting are a Python project convention |
| `.repomixignore` | **Multiple** | Adapt | Each repo that uses repomix gets its own version scoped to that repo's structure |
| `CODE_OF_CONDUCT.md` | **blueprint-repo-blueprints** | Copy as-is | Community standard document; identical across all repos |
| `CONTRIBUTING.md` | **blueprint-repo-blueprints** | Adapt | General contribution guidelines propagate everywhere; product-specific sections removed |
| `LICENSE.md` | **blueprint-repo-blueprints** | Copy as-is | License is identical across all repos |
| `MCP_SETUP.md` | **hoopstat-data** | Copy as-is | MCP proxy setup is specific to the hoopstat data pipeline |
| `README.md` | **Discard** | Rewrite | Every repo gets a new README tailored to its purpose; the monorepo README is not reusable |
| `SECURITY.md` | **blueprint-repo-blueprints** | Copy as-is | Security policy is a community standard; identical across all repos |
| `docker-compose.test.yml` | **hoopstat-data** | Adapt | Integration test orchestration is product-specific; blueprint repos get a generalized version |
| `docs-requirements.txt` | **python-project-blueprint** | Adapt | MkDocs dependencies for documentation generation; generalize package list |
| `mkdocs.yml` | **Multiple** | Adapt | Each repo with docs gets its own `mkdocs.yml`. Blueprint version is a skeleton; hoopstat-data gets the current nav adapted |
| `repomix.config.json` | **Multiple** | Adapt | All repos include repomix config (per project convention); scope output/ignore to each repo's structure |

## `.github/` Directory

### `.github/` Root Files

| File | Destination | Action | Rationale |
|---|---|---|---|
| `.github/copilot-instructions.md` | **Multiple** | Adapt | Each repo needs AI contributor instructions tailored to its structure and conventions |
| `.github/dependabot.yml` | **Multiple** | Adapt | Each repo configures Dependabot for its own dependency directories |
| `.github/logo.svg` | **hoopstat-app** | Copy as-is | Product logo; belongs with the frontend/branding repo |
| `.github/pull_request_template.md` | **blueprint-repo-blueprints** | Copy as-is | PR template is a general development convention |

### `.github/ISSUE_TEMPLATE/`

| File | Destination | Action | Rationale |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/bug-report.yml` | **blueprint-repo-blueprints** | Copy as-is | Standard issue template usable across all repos |
| `.github/ISSUE_TEMPLATE/config.yml` | **blueprint-repo-blueprints** | Copy as-is | Issue template configuration is generic |
| `.github/ISSUE_TEMPLATE/feature-request.yml` | **blueprint-repo-blueprints** | Copy as-is | Standard feature request template usable across all repos |

### `.github/actions/`

| File | Destination | Action | Rationale |
|---|---|---|---|
| `.github/actions/setup-python-poetry/action.yml` | **python-project-blueprint** | Copy as-is | Reusable action for Python + Poetry setup; core to all Python repos |

### `.github/workflows/`

| File | Destination | Action | Rationale |
|---|---|---|---|
| `workflows/accept-adrs.yml` | **blueprint-repo-blueprints** | Copy as-is | ADR acceptance workflow is a general convention for any repo using ADRs |
| `workflows/build-database.yml` | **hoopstat-data** | Copy as-is | Database compilation is product-specific (DuckDB/SQLite from Gold JSON) |
| `workflows/ci.yml` | **Multiple** | Adapt | Core CI workflow. **python-project-blueprint** gets a generalized version (lint/test/build for apps+libs). **hoopstat-data** gets the current version adapted for its apps |
| `workflows/daily-ingestion.yml` | **hoopstat-data** | Copy as-is | Scheduled NBA data ingestion is fully product-specific |
| `workflows/data-dictionary.yml` | **hoopstat-data** | Copy as-is | Data dictionary generation is product-specific |
| `workflows/dependabot-auto-merge.yml` | **blueprint-repo-blueprints** | Copy as-is | Dependabot auto-merge is a general convenience workflow |
| `workflows/deploy-frontend.yml` | **hoopstat-app** | Adapt | Frontend deployment adapted to standalone frontend repo structure |
| `workflows/deploy.yml` | **hoopstat-data** | Adapt | Lambda deployment workflow adapted for hoopstat-data repo structure |
| `workflows/documentation.yml` | **python-project-blueprint** | Adapt | MkDocs build/deploy workflow generalized for any Python project with docs |
| `workflows/health-aggregator.yml` | **hoopstat-data** | Copy as-is | Health aggregator pipeline step is product-specific |
| `workflows/infrastructure.yml` | **hoopstat-data** | Adapt | Terraform deployment adapted for hoopstat-data repo paths. **python-aws-data-blueprint** gets a generalized scaffold |
| `workflows/publish-mcp-proxy.yml` | **hoopstat-data** | Copy as-is | MCP proxy publishing is product-specific |
| `workflows/quarantine-replay.yml` | **hoopstat-data** | Copy as-is | Quarantine replay is product-specific pipeline functionality |
| `workflows/quarantine-status.yml` | **hoopstat-data** | Copy as-is | Quarantine status reporting is product-specific |
| `workflows/reusable-build-push.yml` | **python-project-blueprint** | Adapt | Reusable Docker build+push workflow; generalize for any Python app with ECR |
| `workflows/silver-processing.yml` | **hoopstat-data** | Copy as-is | Silver processing pipeline step is product-specific |
| `workflows/validate-dependabot.yml` | **blueprint-repo-blueprints** | Copy as-is | Dependabot validation is a general CI convenience |

## `apps/` Directory

All applications are product-specific and move to **hoopstat-data**. Blueprint repos get example app scaffolding derived from the templates.

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `apps/README.md` | **hoopstat-data** | Adapt | Update to reflect apps in hoopstat-data only |
| `apps/bronze-ingestion/` | **hoopstat-data** | Copy as-is | NBA data ingestion app — fully product-specific |
| `apps/db-compiler/` | **hoopstat-data** | Copy as-is | Database compilation app — fully product-specific |
| `apps/gold-analytics/` | **hoopstat-data** | Copy as-is | Gold layer analytics app — fully product-specific |
| `apps/health-aggregator/` | **hoopstat-data** | Copy as-is | Health dashboard aggregator — fully product-specific |
| `apps/mcp-local-proxy/` | **hoopstat-data** | Copy as-is | MCP local proxy — product-specific tool |
| `apps/silver-processing/` | **hoopstat-data** | Copy as-is | Silver processing app — fully product-specific |

**Blueprint scaffolding note:** **python-project-blueprint** and **python-aws-data-blueprint** get an empty `apps/` directory with a scaffold app generated from `templates/python-app-template/`.

## `libs/` Directory

All libraries are product-specific and move to **hoopstat-data**. Blueprint repos get example lib scaffolding derived from the templates.

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `libs/README.md` | **hoopstat-data** | Adapt | Update to reflect libs in hoopstat-data only |
| `libs/hoopstat-config/` | **hoopstat-data** | Copy as-is | Config management library — product-specific but reusable patterns |
| `libs/hoopstat-data/` | **hoopstat-data** | Copy as-is | Core data models library (bronze, silver, gold, health models) |
| `libs/hoopstat-e2e-testing/` | **hoopstat-data** | Copy as-is | E2E testing utilities with LocalStack — product-specific |
| `libs/hoopstat-mock-data/` | **hoopstat-data** | Copy as-is | Mock data generation for NBA stats — product-specific |
| `libs/hoopstat-nba_api/` | **hoopstat-data** | Copy as-is | NBA API client wrapper — product-specific |
| `libs/hoopstat-observability/` | **hoopstat-data** | Copy as-is | Observability library (JSON logging, correlation, diagnostics) |
| `libs/hoopstat-s3/` | **hoopstat-data** | Copy as-is | S3 upload/management utilities — product-specific |

**Blueprint scaffolding note:** **python-project-blueprint** and **python-aws-data-blueprint** get an empty `libs/` directory with a scaffold library generated from `templates/python-lib-template/`.

## `frontend-app/` Directory

The frontend application is product-specific and moves to **hoopstat-app**. A generalized template version goes to **static-js-app-blueprint**.

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `frontend-app/.gitignore` | **hoopstat-app** | Copy as-is | Frontend-specific gitignore |
| `frontend-app/README.md` | **hoopstat-app** | Adapt | Update for standalone frontend repo context |
| `frontend-app/assets/favicon.svg` | **hoopstat-app** | Copy as-is | Product-specific branding asset |
| `frontend-app/assets/styles.css` | **hoopstat-app** | Copy as-is | Product-specific styles |
| `frontend-app/health.html` | **hoopstat-app** | Copy as-is | Product-specific health dashboard page |
| `frontend-app/index.html` | **hoopstat-app** | Copy as-is | Product-specific main page |
| `frontend-app/scripts/app.js` | **hoopstat-app** | Copy as-is | Product-specific application JavaScript |
| `frontend-app/scripts/health.js` | **hoopstat-app** | Copy as-is | Product-specific health dashboard JavaScript |

**Blueprint note:** **static-js-app-blueprint** gets a generalized version of the frontend-app structure with placeholder content, generic styles, and example JavaScript. The structure (assets/, scripts/, index.html) is preserved but all hoopstat-specific content is replaced with template examples.

## `infrastructure/` Directory

Infrastructure is product-specific and moves to **hoopstat-data**. A Terraform scaffolding version goes to **python-aws-data-blueprint**.

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `infrastructure/.gitignore` | **hoopstat-data** | Copy as-is | Terraform gitignore |
| `infrastructure/.terraform-version` | **hoopstat-data** | Copy as-is | Terraform version pinning |
| `infrastructure/GITHUB_ACTIONS_ROLE.md` | **Multiple** | Adapt | OIDC role setup guide. **hoopstat-data** gets the current version; **python-aws-data-blueprint** gets a generalized version |
| `infrastructure/LAMBDA_DEPLOYMENT.md` | **hoopstat-data** | Copy as-is | Product-specific Lambda deployment guide |
| `infrastructure/PUBLIC_ACCESS_GUIDE.md` | **hoopstat-data** | Copy as-is | Product-specific S3/CloudFront public access guide |
| `infrastructure/README.md` | **hoopstat-data** | Adapt | Update for standalone repo context |
| `infrastructure/SETUP.md` | **Multiple** | Adapt | Terraform setup guide. **hoopstat-data** gets current version; **python-aws-data-blueprint** gets a generalized version |
| `infrastructure/backend.tf` | **hoopstat-data** | Copy as-is | Terraform backend config — product-specific S3 state bucket |
| `infrastructure/main.tf` | **hoopstat-data** | Copy as-is | Core Terraform config — all resources are product-specific |
| `infrastructure/observability_README.md` | **hoopstat-data** | Copy as-is | CloudWatch observability guide — product-specific |
| `infrastructure/outputs.tf` | **hoopstat-data** | Copy as-is | Terraform outputs — product-specific |
| `infrastructure/variables.tf` | **hoopstat-data** | Copy as-is | Terraform variables — product-specific |
| `infrastructure/versions.tf` | **hoopstat-data** | Copy as-is | Terraform provider versions |
| `infrastructure/tests/` | **hoopstat-data** | Copy as-is | Infrastructure tests — product-specific |

**Blueprint note:** **python-aws-data-blueprint** gets a minimal Terraform scaffold with `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf` containing commented examples and placeholder resource definitions for S3 + Lambda + IAM.

## `templates/` Directory

The Python app/lib templates are the primary content for **python-project-blueprint**.

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `templates/python-app-template/` | **python-project-blueprint** | Adapt | Python app template; generalize any remaining hoopstat references. This becomes the canonical app scaffold in the blueprint |
| `templates/python-lib-template/` | **python-project-blueprint** | Adapt | Python lib template with `{{LIBRARY_NAME}}`/`{{MODULE_NAME}}` placeholders; already generalized. Minor updates for standalone repo context |

## `meta/` Directory

### `meta/` Root Files

| File | Destination | Action | Rationale |
|---|---|---|---|
| `meta/DEVELOPMENT_PHILOSOPHY.md` | **blueprint-repo-blueprints** | Copy as-is | Core development philosophy; propagated identically to all derived repos |
| `meta/DATA_AVAILABILITY_POLICY.md` | **hoopstat-data** | Copy as-is | Product-specific data availability policy |
| `meta/GOLD_LAYER_ANALYTICS_STRATEGY.md` | **hoopstat-data** | Copy as-is | Product-specific analytics strategy |
| `meta/PROJECT_EVALUATION_REPORT.md` | **Discard** | — | Historical evaluation of the monorepo; not relevant post-migration |
| `meta/ROBOT_ETHICS.md` | **blueprint-repo-blueprints** | Copy as-is | AI ethics policy; applies to all repos using AI contributors |
| `meta/SIMPLIFIED_ROADMAP.md` | **Discard** | — | Monorepo roadmap; each new repo gets its own roadmap |

### `meta/adr/` — Architecture Decision Records

ADRs are split between general development conventions (blueprint repos) and product-specific decisions (hoopstat-data). General ADRs are adapted to remove hoopstat-specific context.

| File | Title | Destination | Action | Rationale |
|---|---|---|---|---|
| `ADR-001-use_adrs.md` | Use ADRs | **blueprint-repo-blueprints** | Adapt | General convention; remove hoopstat-specific examples |
| `ADR-002-python_version.md` | Python 3.12+ | **python-project-blueprint** | Copy as-is | Python version decision applies to all Python repos |
| `ADR-003-poetry_deps.md` | Use Poetry | **python-project-blueprint** | Copy as-is | Poetry dependency management applies to all Python repos |
| `ADR-004-pytest_testing.md` | Use pytest | **python-project-blueprint** | Copy as-is | pytest convention applies to all Python repos |
| `ADR-005-ruff_black.md` | Ruff + Black | **python-project-blueprint** | Copy as-is | Linting/formatting applies to all Python repos |
| `ADR-006-docker_containers.md` | Docker Containers | **python-project-blueprint** | Copy as-is | Docker containerization applies to all Python apps |
| `ADR-007-github_actions.md` | GitHub Actions CI/CD | **blueprint-repo-blueprints** | Adapt | General CI/CD convention; adapt examples for multi-repo context |
| `ADR-008-monorepo_apps.md` | Monorepo /apps Structure | **python-project-blueprint** | Adapt | Apps directory structure carries forward; update to reflect single-project focus |
| `ADR-009-aws_cloud.md` | AWS Cloud Provider | **python-aws-data-blueprint** | Copy as-is | AWS decision applies to AWS-specific blueprint |
| `ADR-010-terraform_iac.md` | Terraform IaC | **python-aws-data-blueprint** | Copy as-is | Terraform decision applies to AWS-specific blueprint |
| `ADR-011-github_oidc.md` | GitHub OIDC Auth | **python-aws-data-blueprint** | Copy as-is | OIDC authentication applies to AWS-specific blueprint |
| `ADR-012-single_env.md` | Single Environment | **hoopstat-data** | Copy as-is | Environment strategy is product-specific |
| `ADR-013-nba_api_data.md` | NBA API Data Source | **hoopstat-data** | Copy as-is | NBA API selection is fully product-specific |
| `ADR-014-parquet_storage.md` | Parquet Storage (Superseded) | **hoopstat-data** | Copy as-is | Historical product-specific decision |
| `ADR-015-json_logging.md` | JSON Logging | **python-project-blueprint** | Copy as-is | Logging strategy applies to all Python repos |
| `ADR-016-shared_library_versioning.md` | Shared Library Versioning | **python-project-blueprint** | Adapt | Versioning strategy applies but needs context update for multi-repo |
| `ADR-017-infrastructure_deployment_workflow.md` | Infra Deployment Workflow | **hoopstat-data** | Copy as-is | Product-specific deployment workflow |
| `ADR-018-cloudwatch_observability.md` | CloudWatch Observability | **hoopstat-data** | Copy as-is | Product-specific observability stack |
| `ADR-019-frontend-vanilla-approach.md` | Vanilla Frontend | **static-js-app-blueprint** | Adapt | Frontend approach applies to JS blueprint; remove hoopstat-specific context |
| `ADR-020-gold_layer_data_partitioning.md` | Gold Layer Partitioning | **hoopstat-data** | Copy as-is | Product-specific data partitioning |
| `ADR-021-tenacity_retry_logic.md` | Tenacity Retry Logic | **python-project-blueprint** | Copy as-is | Retry pattern applies to all Python repos |
| `ADR-022-click_cli_framework.md` | Click CLI Framework | **python-project-blueprint** | Copy as-is | CLI framework applies to all Python repos |
| `ADR-023-mkdocs_documentation.md` | MkDocs Documentation | **python-project-blueprint** | Copy as-is | Documentation tooling applies to all Python repos |
| `ADR-024-metadata_catalog.md` | Metadata Catalog | **hoopstat-data** | Copy as-is | Product-specific data catalog strategy |
| `ADR-025-json_storage_mvp.md` | JSON Storage MVP | **hoopstat-data** | Copy as-is | Product-specific storage decision |
| `ADR-026-s3_tables_gold_layer.md` | S3 Tables Gold Layer | **hoopstat-data** | Copy as-is | Product-specific architecture decision |
| `ADR-027-hybrid_gold_architecture.md` | Stateless Gold Access | **hoopstat-data** | Copy as-is | Product-specific architecture decision |
| `ADR-028-gold_layer_final.md` | Gold Layer Final | **hoopstat-data** | Copy as-is | Product-specific architecture decision |
| `ADR-029-piwheels_optimization.md` | Piwheels ARM Builds | **python-project-blueprint** | Copy as-is | ARM build optimization applies to all Python Docker builds |
| `ADR-030-cost_optimized_observability.md` | Cost-Optimized Observability | **hoopstat-data** | Copy as-is | Product-specific observability decision |
| `ADR-031-bronze_game_file_granularity.md` | Bronze File Granularity | **hoopstat-data** | Copy as-is | Product-specific data pipeline decision |
| `ADR-032-s3_object_key_naming.md` | S3 Key Naming | **hoopstat-data** | Copy as-is | Product-specific S3 key convention |
| `ADR-033-local_proxy_mcp_architecture.md` | Local Proxy MCP | **hoopstat-data** | Copy as-is | Product-specific MCP architecture |
| `ADR-034-dual_runtime_mcp_adapter.md` | Dual-Runtime MCP | **hoopstat-data** | Copy as-is | Product-specific MCP adapter decision |
| `ADR-035-gold_s3_public_access.md` | Gold S3 Public Access | **hoopstat-data** | Copy as-is | Product-specific access decision |
| `ADR-036-lightweight_charting_library.md` | Chart.js via CDN | **hoopstat-app** | Copy as-is | Frontend charting library — product-specific |
| `ADR-037-quarantine_error_classification.md` | Quarantine Classification | **hoopstat-data** | Copy as-is | Product-specific error handling decision |
| `ADR-038-cloudfront-cache-tuning.md` | CloudFront Cache Tuning | **hoopstat-data** | Copy as-is | Product-specific cache tuning |
| `ADR-040-static-pipeline-health-dashboard.md` | Static Health Dashboard | **hoopstat-data** | Copy as-is | Product-specific dashboard architecture |
| `ADR-041-static-database-artifacts.md` | Static Database Artifacts | **hoopstat-data** | Copy as-is | Product-specific DuckDB/SQLite decision |
| `TEMPLATE.md` | **blueprint-repo-blueprints** | Copy as-is | ADR template is a general convention for any repo using ADRs |

### `meta/plans/` — Planning Documents

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `meta/plans/bronze-to-silver-etl-pipeline.md` | **hoopstat-data** | Copy as-is | Product-specific pipeline plan |
| `meta/plans/local-proxy-mcp-architecture.md` | **hoopstat-data** | Copy as-is | Product-specific MCP architecture plan |
| `meta/plans/mcp-server-architecture.md` | **hoopstat-data** | Copy as-is | Product-specific MCP server plan |
| `meta/plans/medallion-data-architecture.md` | **hoopstat-data** | Copy as-is | Product-specific medallion architecture plan |
| `meta/plans/silver-to-gold-etl-jobs.md` | **hoopstat-data** | Copy as-is | Product-specific ETL plan |
| `meta/plans/stateless-gold-access-plan.md` | **hoopstat-data** | Copy as-is | Product-specific gold access plan |
| `meta/plans/v1-architecture-diagram.md` | **hoopstat-data** | Copy as-is | Product-specific architecture diagram |
| `meta/plans/v2-architecture-diagram.md` | **hoopstat-data** | Copy as-is | Product-specific architecture diagram |
| `meta/plans/future/` | **hoopstat-data** | Copy as-is | Future plans are product-specific (MCP client, E2E testing, frontend design) |
| `meta/plans/multi-epic-migration/` | **Discard** | — | Migration planning artifacts; historical to hoopstat-haus only |

## `scripts/` Directory

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `scripts/README.md` | **hoopstat-data** | Adapt | Update to reflect scripts relevant to hoopstat-data only |
| `scripts/build-docs.sh` | **python-project-blueprint** | Adapt | MkDocs build script; generalize paths for any Python project |
| `scripts/check-docs.sh` | **python-project-blueprint** | Adapt | MkDocs check script; generalize paths |
| `scripts/ecr-helper.sh` | **hoopstat-data** | Copy as-is | ECR helper is product-specific (AWS account, repo names) |
| `scripts/generate-data-dictionary.py` | **hoopstat-data** | Copy as-is | Data dictionary generation is product-specific (references hoopstat models) |
| `scripts/generate-db-schema-docs.py` | **hoopstat-data** | Copy as-is | DB schema doc generation is product-specific |
| `scripts/generate-docs.py` | **hoopstat-data** | Copy as-is | Docs generation references product-specific model modules |
| `scripts/local-ci-check.sh` | **python-project-blueprint** | Adapt | Local CI check script; generalize for any Python app/lib structure |
| `scripts/setup-local-deps.py` | **python-project-blueprint** | Adapt | Dependency setup script; generalize app/lib discovery |
| `scripts/test-health-dashboard.sh` | **hoopstat-data** | Copy as-is | Health dashboard test script is product-specific |
| `scripts/test-orchestration.md` | **hoopstat-data** | Copy as-is | Orchestration testing guide is product-specific |
| `scripts/tests/` | **hoopstat-data** | Copy as-is | Script tests reference product-specific data dictionary logic |
| `scripts/validate-orchestration.sh` | **hoopstat-data** | Copy as-is | Orchestration validation is product-specific |

## `docs-src/` Directory

Documentation source files are split between general development docs (blueprint repos) and product-specific docs (hoopstat-data).

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `docs-src/index.md` | **Multiple** | Adapt | Each repo gets its own docs index page |
| `docs-src/BUILD_ORCHESTRATION.md` | **hoopstat-data** | Copy as-is | Build orchestration is product-specific |
| `docs-src/CONTRIBUTING.md` | **blueprint-repo-blueprints** | Adapt | General contributing guide; remove product-specific references |
| `docs-src/DATABASE_GUIDE.md` | **hoopstat-data** | Copy as-is | DuckDB/SQLite database guide is product-specific |
| `docs-src/DATA_DICTIONARY.md` | **hoopstat-data** | Copy as-is | Data dictionary is product-specific |
| `docs-src/DEVELOPMENT_PHILOSOPHY.md` | **blueprint-repo-blueprints** | Copy as-is | Core philosophy propagated to all repos (same as `meta/` version) |
| `docs-src/DOCUMENTATION_README.md` | **python-project-blueprint** | Adapt | MkDocs documentation guide; generalize for any Python project |
| `docs-src/E2E_TESTING.md` | **hoopstat-data** | Copy as-is | E2E testing guide is product-specific |
| `docs-src/ECR_IMAGE_MANAGEMENT.md` | **hoopstat-data** | Copy as-is | ECR image management is product-specific |
| `docs-src/HEALTH_DASHBOARD_RUNBOOK.md` | **hoopstat-data** | Copy as-is | Health dashboard runbook is product-specific |
| `docs-src/JSON_ARTIFACT_SCHEMAS.md` | **hoopstat-data** | Copy as-is | JSON artifact schemas are product-specific |
| `docs-src/LOCAL_DEVELOPMENT_DEPENDENCIES.md` | **python-project-blueprint** | Adapt | Local dev dependency guide; generalize tool list |
| `docs-src/SHARED_LIBRARY_VERSIONING.md` | **python-project-blueprint** | Adapt | Library versioning guide; update for multi-repo context |
| `docs-src/feature-request-automation.md` | **blueprint-repo-blueprints** | Adapt | Feature request workflow guide; generalize |
| `docs-src/libraries/` | **hoopstat-data** | Adapt | Library documentation pages reference hoopstat-specific libraries; update index for standalone repo |

## `testing/` Directory

| Path | Destination | Action | Rationale |
|---|---|---|---|
| `testing/Dockerfile.test` | **hoopstat-data** | Adapt | Integration test Docker config; update paths for standalone repo |
| `testing/tests/test_integration_pipeline.py` | **hoopstat-data** | Copy as-is | Integration pipeline test is product-specific |
| `testing/validate_e2e_framework.py` | **hoopstat-data** | Copy as-is | E2E framework validation is product-specific |

---

## Summary by Destination

### blueprint-repo-blueprints

Core files that propagate to every derived repository:

- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` (adapt), `LICENSE.md`, `SECURITY.md`
- `meta/DEVELOPMENT_PHILOSOPHY.md`, `meta/ROBOT_ETHICS.md`
- `meta/adr/TEMPLATE.md`, `ADR-001` (adapt), `ADR-007` (adapt)
- `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`
- `workflows/accept-adrs.yml`, `workflows/dependabot-auto-merge.yml`, `workflows/validate-dependabot.yml`
- `docs-src/CONTRIBUTING.md` (adapt), `docs-src/DEVELOPMENT_PHILOSOPHY.md`, `docs-src/feature-request-automation.md` (adapt)

### static-js-app-blueprint

- Generalized version of `frontend-app/` structure (scaffold)
- `ADR-019` (adapt — vanilla frontend approach)
- Generalized `workflows/deploy-frontend.yml` (scaffold)

### python-project-blueprint

- `templates/python-app-template/` (adapt), `templates/python-lib-template/` (adapt)
- `.dockerignore` (adapt), `.pre-commit-config.yaml`
- `.github/actions/setup-python-poetry/action.yml`
- `workflows/ci.yml` (adapt), `workflows/reusable-build-push.yml` (adapt), `workflows/documentation.yml` (adapt)
- `docs-requirements.txt` (adapt), `mkdocs.yml` (adapt)
- `scripts/build-docs.sh` (adapt), `scripts/check-docs.sh` (adapt), `scripts/local-ci-check.sh` (adapt), `scripts/setup-local-deps.py` (adapt)
- ADRs: 002, 003, 004, 005, 006, 008 (adapt), 015, 016 (adapt), 021, 022, 023, 029
- `docs-src/DOCUMENTATION_README.md` (adapt), `docs-src/LOCAL_DEVELOPMENT_DEPENDENCIES.md` (adapt), `docs-src/SHARED_LIBRARY_VERSIONING.md` (adapt)

### python-aws-data-blueprint

- Terraform scaffold from `infrastructure/` structure
- `infrastructure/GITHUB_ACTIONS_ROLE.md` (adapt), `infrastructure/SETUP.md` (adapt)
- `workflows/infrastructure.yml` (adapt — scaffold)
- ADRs: 009, 010, 011

### hoopstat-data

- All `apps/` content (6 apps — copy as-is)
- All `libs/` content (7 libraries — copy as-is)
- All `infrastructure/` content (copy as-is)
- All `testing/` content
- Product-specific `scripts/` (ecr-helper, generate-data-dictionary, generate-db-schema-docs, generate-docs, test-health-dashboard, test-orchestration, validate-orchestration)
- Product-specific `docs-src/` (DATABASE_GUIDE, DATA_DICTIONARY, E2E_TESTING, ECR_IMAGE_MANAGEMENT, HEALTH_DASHBOARD_RUNBOOK, JSON_ARTIFACT_SCHEMAS, BUILD_ORCHESTRATION, libraries/)
- Product-specific `meta/` files (DATA_AVAILABILITY_POLICY, GOLD_LAYER_ANALYTICS_STRATEGY)
- Product-specific plans (`meta/plans/` — all except multi-epic-migration)
- Product-specific ADRs: 012–014, 017–018, 020, 024–028, 030–035, 037–038, 040–041
- `MCP_SETUP.md`, `docker-compose.test.yml` (adapt)

### hoopstat-app

- All `frontend-app/` content (copy as-is)
- `.github/logo.svg`
- `ADR-036` (Chart.js via CDN)
- `workflows/deploy-frontend.yml` (adapt)

### Discard

- `README.md` — Rewritten per-repo
- `meta/PROJECT_EVALUATION_REPORT.md` — Historical monorepo evaluation
- `meta/SIMPLIFIED_ROADMAP.md` — Monorepo roadmap; replaced per-repo
- `meta/plans/multi-epic-migration/` — Migration planning artifacts; historical to hoopstat-haus

### Multiple (requires per-repo adaptation)

| File | Repos | Notes |
|---|---|---|
| `.gitignore` | All repos | Python repos share Python rules; frontend repo gets JS rules; each adds repo-specific entries |
| `.repomixignore` | All repos | Scoped to each repo's file structure |
| `repomix.config.json` | All repos | Output filename and ignore patterns adjusted per repo |
| `.github/copilot-instructions.md` | All repos | AI instructions tailored to each repo's structure and conventions |
| `.github/dependabot.yml` | All repos with dependencies | Directory paths updated per repo structure |
| `mkdocs.yml` | All repos with docs | Navigation and site name adjusted per repo |
| `docs-src/index.md` | All repos with docs | Landing page content specific to each repo |
| `workflows/ci.yml` | python-project-blueprint, hoopstat-data | Blueprint gets generalized version; hoopstat-data gets current version adapted |
| `infrastructure/GITHUB_ACTIONS_ROLE.md` | hoopstat-data, python-aws-data-blueprint | Product-specific vs. generalized |
| `infrastructure/SETUP.md` | hoopstat-data, python-aws-data-blueprint | Product-specific vs. generalized |
| `workflows/infrastructure.yml` | hoopstat-data, python-aws-data-blueprint | Product-specific vs. scaffold |
| `docker-compose.test.yml` | hoopstat-data, python-project-blueprint | Product-specific vs. generalized scaffold |
