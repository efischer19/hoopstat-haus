# feat: Adapt CI/CD workflows for hoopstat-data

## What do you want to build?

Migrate and adapt the GitHub Actions workflows from hoopstat-haus to hoopstat-data. Each workflow needs to be updated for the new repository context, including OIDC role ARNs, ECR repository names, and trigger paths.

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` — Linting, testing for all apps and libs (adapted paths)
- [ ] `.github/workflows/deploy.yml` — ECR build/push and Lambda deployment
- [ ] `.github/workflows/infrastructure.yml` — Terraform plan/apply
- [ ] `.github/workflows/daily-ingestion.yml` — Scheduled bronze ingestion (cron trigger, initially disabled)
- [ ] `.github/workflows/silver-processing.yml` — Silver layer processing trigger
- [ ] `.github/workflows/build-database.yml` — DuckDB/SQLite compilation
- [ ] `.github/workflows/health-aggregator.yml` — Health metrics aggregation
- [ ] `.github/workflows/publish-mcp-proxy.yml` — MCP proxy PyPI publication
- [ ] `.github/workflows/reusable-build-push.yml` — Reusable Docker build/push action
- [ ] `.github/workflows/documentation.yml` — MkDocs documentation build/deploy
- [ ] `.github/workflows/data-dictionary.yml` — Data dictionary generation
- [ ] `.github/workflows/quarantine-status.yml` — Quarantine status reporting (copy as-is per file-mapping)
- [ ] `.github/workflows/quarantine-replay.yml` — Quarantine error replay (copy as-is per file-mapping)
- [ ] `.github/workflows/accept-adrs.yml` — ADR status validation
- [ ] `.github/workflows/dependabot-auto-merge.yml` — Auto-merge dependabot PRs (inherited from blueprint, verify present)
- [ ] `.github/workflows/validate-dependabot.yml` — Validate dependabot PRs (inherited from blueprint, verify present)
- [ ] `.github/dependabot.yml` — Updated with all app/lib directories
- [ ] All workflows reference the correct OIDC role (via repository variable, not hardcoded)
- [ ] All workflows use the correct ECR repository names
- [ ] All scheduled workflows are initially disabled (remove cron trigger or comment it out)
- [ ] The CI workflow passes on the migrated code

## Implementation Notes (Optional)

Workflow migration approach:
1. Copy each workflow from hoopstat-haus
2. Update trigger paths (if any use path filters)
3. Replace hardcoded OIDC role ARNs with `${{ vars.AWS_ROLE_ARN }}` or similar
4. Replace hardcoded ECR repo names with variables
5. Verify syntax with `actionlint` or similar if available
6. Test CI workflow first (it doesn't need AWS credentials)

**Scheduled workflows** (daily-ingestion, etc.) should be disabled initially by:
- Commenting out the `schedule` trigger
- Keeping only `workflow_dispatch` for manual testing
- They'll be re-enabled in Epic 9 after deployment is validated

**Workflow that does NOT go to hoopstat-data:**
- `deploy-frontend.yml` — Goes to hoopstat-app (adapted for standalone frontend repo)

**Workflows confirmed in scope per file-mapping:**
- `quarantine-status.yml` and `quarantine-replay.yml` — Copy as-is to hoopstat-data (product-specific pipeline functionality)
- `data-dictionary.yml` — Copy as-is to hoopstat-data (product-specific)
- `build-database.yml` — Copy as-is to hoopstat-data (product-specific DuckDB/SQLite compilation)
- `dependabot-auto-merge.yml` and `validate-dependabot.yml` — These originate from blueprint-repo-blueprints and should already be present from template inheritance. Verify they exist and function correctly.

Create `.github/actions/setup-python-poetry/action.yml` as a reusable composite action (copy from hoopstat-haus, it should be identical).
