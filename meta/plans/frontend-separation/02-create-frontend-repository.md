# Ticket 02: Create and Populate hoopstat-haus-frontend Repository

**Title:** `feat: create hoopstat-haus-frontend repo and migrate frontend code`

## What do you want to build?

Create the `hoopstat-haus-frontend` GitHub repository as a template-child of `static-js-aws-monorepo-template` and migrate all user-facing frontend code from this repo's `frontend-app/` directory.

The new repository should contain a working static site with its own CI/CD pipeline that can deploy to the existing CloudFront distribution.

### Files to migrate

| Source (this repo) | Destination (new repo) |
|---|---|
| `frontend-app/index.html` | `src/index.html` (or template-appropriate path) |
| `frontend-app/assets/styles.css` | `src/assets/styles.css` |
| `frontend-app/assets/favicon.svg` | `src/assets/favicon.svg` |
| `frontend-app/scripts/app.js` | `src/scripts/app.js` |
| `frontend-app/README.md` | `README.md` (adapted) |
| `frontend-app/.gitignore` | `.gitignore` (merged with template) |

### Files that do NOT migrate (they stay here)

| File | Reason |
|---|---|
| `frontend-app/health.html` | Backend observability (ADR-040, Ticket 03) |
| `frontend-app/scripts/health.js` | Backend observability (ADR-040, Ticket 03) |

## Acceptance Criteria

- [ ] `hoopstat-haus-frontend` repository exists on GitHub under the same owner (`efischer19`)
- [ ] Repository is created from `static-js-aws-monorepo-template` (or manually if template is not ready)
- [ ] All user-facing frontend files (`index.html`, `app.js`, `styles.css`, `favicon.svg`) are present in the new repo
- [ ] The new repo has a working local development setup (e.g., `python -m http.server` or template-provided dev server)
- [ ] A deployment workflow exists in the new repo that syncs files to `s3://hoopstat-haus-gold/served/` (HTML, assets, scripts)
- [ ] The deployed site is accessible via the existing CloudFront URL and renders correctly
- [ ] `health.html` and `health.js` are NOT in the new repo
- [ ] The new repo's README documents the project, references the data backend repo, and explains the CloudFront deployment model

## Implementation Notes (Optional)

- The exact directory structure in the new repo depends on the template's conventions. Adapt as needed.
- The `CONFIG.GOLD_BASE_URL` in `app.js` should continue pointing to the same CloudFront domain — no URL changes are needed since both repos deploy to the same distribution.
- If the template is not ready, create a minimal repo manually with: the migrated files, a `.github/workflows/deploy.yml` workflow, and a README. Retroactively adopt the template later.
- Consider preserving git history for the migrated files using `git filter-branch` or `git subtree split`, but this is optional — the files are small and the history is short.
- This ticket is scoped to the **new repo**. Removal of files from **this repo** is handled in Ticket 05.
