# Ticket 05: Remove Frontend Code and Deployment Workflow

**Title:** `feat: remove frontend-app code and deploy-frontend workflow`

## What do you want to build?

Cleanly remove all frontend application code and its deployment workflow from this repository, now that the code has been migrated to `hoopstat-haus-frontend` (Ticket 02) and the health dashboard has been decoupled (Ticket 03).

### Files to remove

| File/Directory | Reason |
|---|---|
| `frontend-app/index.html` | Migrated to new repo |
| `frontend-app/assets/styles.css` | Migrated to new repo |
| `frontend-app/assets/favicon.svg` | Migrated to new repo |
| `frontend-app/scripts/app.js` | Migrated to new repo |
| `frontend-app/README.md` | Migrated to new repo |
| `frontend-app/.gitignore` | No longer needed |
| `.github/workflows/deploy-frontend.yml` | Replaced by new repo's workflow |

### Files to relocate (NOT remove)

| File | New Location | Reason |
|---|---|---|
| `frontend-app/health.html` | `health-dashboard/health.html` (or similar) | Backend observability, per Ticket 03 |
| `frontend-app/scripts/health.js` | `health-dashboard/health.js` (or similar) | Backend observability, per Ticket 03 |

### Directory cleanup

After removal, the `frontend-app/` directory should be completely deleted. The health dashboard files should live in a new top-level directory (e.g., `health-dashboard/`) or within `apps/health-aggregator/static/`.

## Acceptance Criteria

- [ ] `frontend-app/` directory no longer exists in the repository
- [ ] `.github/workflows/deploy-frontend.yml` no longer exists
- [ ] Health dashboard files (`health.html`, `health.js`) are present in their new location and still deployable
- [ ] No broken references to `frontend-app/` remain in any file (grep for `frontend-app` across the repo)
- [ ] CI passes — no workflows reference removed files
- [ ] The CloudFront-served site continues to work (frontend files are now deployed by the new repo; health files by this repo)
- [ ] `git log --oneline --all -- frontend-app/` confirms the removal commit

## Implementation Notes (Optional)

- **Prerequisite:** This ticket depends on Ticket 02 (new repo is live and deploying) and Ticket 03 (health dashboard is decoupled). Do not remove files until the new repo is confirmed to be deploying successfully.

- **Health file relocation:** The exact new location for health files should be decided in Ticket 03. Options include:
  - `health-dashboard/` (top-level, simple)
  - `apps/health-aggregator/static/` (co-located with the Lambda)
  - Keep them at repo root as standalone files

- **Grep verification:** After removal, run:
  ```bash
  grep -r "frontend-app" --include="*.md" --include="*.yml" --include="*.yaml" --include="*.tf" .
  ```
  Fix any remaining references (documentation, workflows, Terraform comments).

- **Dependabot:** Check `.github/dependabot.yml` for any `frontend-app/` directory entries. There should be none (vanilla JS has no package manager), but verify.

- This is a straightforward deletion PR. Keep the commit atomic: one commit that removes all frontend files and relocates health files.
