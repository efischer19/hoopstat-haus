# Epic: Separate Frontend to Its Own Repository

## Executive Summary

This epic splits the Hoopstat Haus frontend application (`frontend-app/`) into a new dedicated repository (`hoopstat-haus-frontend`), leaving this repository as a focused Python data backend. The separation is motivated by three factors:

1. **Tooling mismatch:** The backend uses Python tooling (Poetry, Ruff, pytest, Docker) while the frontend is vanilla HTML/CSS/JS. Keeping both in one repo means neither gets optimal CI/CD.
2. **Template alignment:** The `static-js-aws-monorepo-template` repository provides a proven foundation for JavaScript static site projects. The new frontend repo can be a template-child, inheriting its CI/CD and deployment patterns.
3. **Focus:** A Python-only backend repo is easier to reason about, test, and deploy. Frontend changes (styles, charting, UI) don't need to interact with the data pipeline's CI checks.

### What Stays in This Repo

- All Python applications (`apps/`), shared libraries (`libs/`), and their tests
- Terraform infrastructure (`infrastructure/`), including the CloudFront distribution
- The **pipeline health dashboard** (`health.html`, `scripts/health.js`) — this is a backend observability tool, not a consumer-facing frontend feature (see [ADR-040](../../adr/ADR-040-static-pipeline-health-dashboard.md))
- The `deploy-frontend.yml` workflow is removed; health file deployment is folded into the existing health-aggregator or infrastructure workflow
- All data pipeline workflows, documentation, and ADRs

### What Moves to the New Repo

- `frontend-app/index.html`, `frontend-app/assets/`, `frontend-app/scripts/app.js`
- Frontend-specific documentation (`frontend-app/README.md`)
- A new deployment workflow targeting the same S3 bucket and CloudFront distribution
- Ownership of ADR-019 (Vanilla Approach) and ADR-036 (Chart.js) decisions — these are annotated as "Transferred" in this repo

### What Is Shared

- The **S3 bucket** (`hoopstat-haus-gold`) and **CloudFront distribution** remain in this repo's Terraform. Both repos deploy files to the `served/` prefix.
- The **OIDC IAM role** for GitHub Actions is shared or cloned with path-restricted S3 permissions so each repo can only write to its own files.
- The **domain** (`data.hoopstat.haus` or `hoopstat.haus`) continues to point at the single CloudFront distribution.

### Governing Decision

- **ADR-042: Frontend Repository Separation** (Proposed) — documents this decision and its trade-offs.

### Sequencing

The tickets below are ordered for safe, incremental execution. Each ticket is independently mergeable and leaves the system in a working state.

| # | Ticket | Depends On | Repo |
|---|--------|------------|------|
| 01 | Propose ADR-042: Frontend Repository Separation | — | this repo |
| 02 | Create and Populate hoopstat-haus-frontend Repository | 01 | new repo |
| 03 | Retain Health Dashboard as Backend Observability | 01 | this repo |
| 04 | Terraform: Refactor Frontend Cache Behaviors | 03 | this repo |
| 05 | Remove Frontend Code and Deployment Workflow | 02, 04 | this repo |
| 06 | Shared Domain and Cross-Repo Deployment Strategy | 02, 04 | both repos |
| 07 | ADR and Documentation Cleanup | 05, 06 | this repo |

### Risks and Open Questions

1. **Shared S3 bucket writes:** Two repos deploying to the same bucket requires careful IAM scoping. If this proves fragile, the fallback is to give the frontend its own S3 bucket and a second CloudFront distribution (Option 2 in ADR-042).
2. **Cache invalidation coordination:** Frontend deployments need to invalidate CloudFront paths (`/*.html`, `/assets/*`, `/scripts/*`). The new repo's workflow must have permission to create invalidations on the shared distribution.
3. **Template readiness:** The `static-js-aws-monorepo-template` must be mature enough to support the new repo. If it's not ready, the new repo can be created manually and retroactively adopt the template's patterns.
4. **Health dashboard coupling:** `health.js` currently shares `styles.css` with the main frontend. After separation, the health dashboard needs its own minimal styles or an inline `<style>` block.
