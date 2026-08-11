# feat: Migrate frontend-app content to hoopstat-app

## What do you want to build?

Migrate the frontend application from hoopstat-haus's `frontend-app/` directory to the `hoopstat-app` repository. Adapt the file structure to match the template's conventions while preserving all functionality.

## Acceptance Criteria

- [ ] All frontend files are present in `hoopstat-app/src/` (adapted from `frontend-app/`):
  - `index.html` (main analytics dashboard)
  - `health.html` (health dashboard)
  - `assets/styles.css`
  - `assets/favicon.svg`
  - `scripts/app.js`
  - `scripts/health.js`
- [ ] All data source URLs point to the correct CloudFront/S3 endpoints (may be the same as current or updated for new infra)
- [ ] Chart.js CDN references are preserved (ADR-036)
- [ ] No broken links or missing asset references
- [ ] The dashboard renders correctly when served locally (e.g., via `python -m http.server`)
- [ ] Accessibility attributes from the original are preserved
- [ ] `README.md` is updated with hoopstat-app-specific documentation
- [ ] `.github/logo.svg` is present (copy as-is from hoopstat-haus — product-specific branding)
- [ ] ADR-019 (Vanilla HTML/CSS/JS) is present in `meta/adr/` as a project-specific ADR
- [ ] ADR-036 (Chart.js via CDN) is present in `meta/adr/`

## Implementation Notes (Optional)

This is a **copy, not rewrite** operation. The frontend-app code is working and should be brought over intact. The main changes are:

1. **Directory rename:** `frontend-app/` → `src/` (matching the template convention)
2. **Data URLs:** Verify that the JavaScript files reference the correct API/data endpoints. These may need to be updated if the CloudFront distribution changes during migration.
3. **ADR migration:** Copy the frontend-specific ADRs from hoopstat-haus

Refer to the file-mapping document (ticket 01) for the complete list of files to migrate.

The hoopstat-app frontend reads data from the gold layer S3 bucket via CloudFront. During migration, there will be a period where:
- The data is still being written by hoopstat-haus
- The frontend is served from hoopstat-app

This should work as long as the data URLs don't change. If they do change (new CloudFront distribution), update the URLs in the JavaScript files to point to the new endpoints. This coordination is handled in Epic 9.
