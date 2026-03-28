# Ticket 03: Retain Health Dashboard as Backend Observability

**Title:** `feat: decouple health dashboard from frontend-app for backend ownership`

## What do you want to build?

Restructure the health dashboard files (`health.html`, `scripts/health.js`) so they are owned by the backend (this repo) independently of the frontend application. Currently, `health.html` shares `assets/styles.css` with the main frontend, creating a coupling that would break when the frontend is removed.

After this ticket:
- The health dashboard is self-contained and deployable from this repo alone
- It no longer depends on files that will move to the frontend repo
- It is deployed as part of the backend's infrastructure or health-aggregator workflow, not the frontend workflow

## Acceptance Criteria

- [ ] `health.html` renders correctly without any files from the frontend app (`index.html`, `app.js`, `styles.css`, `favicon.svg`)
- [ ] Health dashboard CSS is either inlined in `health.html` or placed in a backend-owned file (e.g., `health/styles.css`)
- [ ] `health.js` continues to fetch `pipeline_health.json` and render the dashboard with Chart.js
- [ ] A deployment mechanism exists in this repo to sync health dashboard files to S3 (either a new workflow, an addition to an existing workflow like `health-aggregator.yml`, or a manual step documented in a runbook)
- [ ] The health dashboard is accessible at its existing CloudFront URL path (`/health.html`) after deployment
- [ ] No functional regression in the health dashboard (traffic-light indicators, Chart.js trends, daily breakdown table all work)

## Implementation Notes (Optional)

- **CSS decoupling approach (choose one):**
  1. **Inline styles:** Extract the subset of `styles.css` that `health.html` uses and inline it via a `<style>` block. This is simplest and keeps the health page fully self-contained (one HTML file + one JS file).
  2. **Separate stylesheet:** Create `health/health-styles.css` with only the health dashboard styles. This is cleaner if the styles are substantial.
  - Recommendation: Inline styles. The health dashboard uses a small subset of the full stylesheet, and a single-file approach aligns with the "observability tool" framing — it should be simple and self-contained.

- **Deployment approach (choose one):**
  1. **Fold into health-aggregator workflow:** The `health-aggregator.yml` workflow already runs after Gold processing. Add a step to sync `health.html` and `scripts/health.js` to S3 alongside the `pipeline_health.json` artifact.
  2. **Dedicated health-dashboard workflow:** A small workflow triggered on changes to health files. Similar to the current `deploy-frontend.yml` but scoped to health files only.
  3. **Infrastructure workflow:** Deploy health files as part of Terraform `null_resource` provisioner or similar.
  - Recommendation: Fold into the health-aggregator workflow for simplicity — it already has the right IAM permissions and deployment context.

- The `frontend-app/` directory structure will be reorganized in Ticket 05. This ticket focuses on making the health dashboard independent *before* the frontend is removed.
- Test locally by serving only the health files (`python -m http.server` from a directory containing just `health.html`, `scripts/health.js`, and a mock `pipeline_health.json`).
