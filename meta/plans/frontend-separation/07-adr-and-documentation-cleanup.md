# Ticket 07: ADR and Documentation Cleanup

**Title:** `feat: clean up ADRs, README, and documentation after frontend separation`

## What do you want to build?

Update all documentation and ADRs in this repository to reflect the post-separation state. This includes annotating frontend-specific ADRs as "Moved", updating the README to remove frontend references, and cleaning up any plans or docs that reference `frontend-app/` as if it's part of this repo.

### ADR changes

| ADR | Current Status | Action |
|---|---|---|
| ADR-019 (Vanilla Frontend) | Accepted | Add note: "Frontend ownership transferred to `hoopstat-haus-frontend`. This ADR remains for historical context." |
| ADR-036 (Chart.js) | Accepted | Add note: "Frontend charting ownership transferred to `hoopstat-haus-frontend`. Chart.js is still used by the health dashboard (`health.html`) in this repo." |
| ADR-040 (Health Dashboard) | Accepted | Update to note that the health dashboard is now backend-owned and deployed independently of the frontend app. |
| ADR-042 (Frontend Separation) | Proposed | Change status to `Accepted` (after human review). |

### Documentation changes

| File | Action |
|---|---|
| `README.md` | Remove `frontend-app/` from repository structure listing. Add a note pointing to the new frontend repo. |
| `meta/plans/future/thin-client-frontend-design.md` | Remove or add a note that this plan now belongs to the frontend repo. |
| `docs-src/` files (if any reference frontend) | Update references to point to the new repo. |
| `CONTRIBUTING.md` | Remove any frontend-specific contribution guidelines. |
| `infrastructure/README.md` | Add documentation about the cross-repo deployment model. |

## Acceptance Criteria

- [ ] ADR-019 has a note indicating frontend ownership has moved to `hoopstat-haus-frontend`
- [ ] ADR-036 has a note indicating frontend charting ownership has moved, while noting health dashboard still uses Chart.js
- [ ] ADR-040 is updated to reflect the health dashboard's backend-only ownership model
- [ ] ADR-042 status is `Accepted` (or remains `Proposed` for human to accept)
- [ ] `README.md` no longer lists `frontend-app/` in the repository structure
- [ ] `README.md` includes a link to the `hoopstat-haus-frontend` repository
- [ ] No file in this repo references `frontend-app/` as an existing directory (verified by grep)
- [ ] `meta/plans/future/thin-client-frontend-design.md` is either removed or annotated
- [ ] `infrastructure/README.md` documents the cross-repo CloudFront deployment model
- [ ] All changes are reviewed and approved by a human maintainer

## Implementation Notes (Optional)

- **ADR annotation format:** Add a blockquote at the top of each affected ADR:
  ```markdown
  > **Note (YYYY-MM-DD):** Frontend application ownership has been transferred to the
  > [`hoopstat-haus-frontend`](https://github.com/efischer19/hoopstat-haus-frontend) repository
  > per ADR-042. This ADR is retained for historical context.
  ```

- **README update:** The repository structure section should be updated from:
  ```
  frontend-app/   # Static web application
  ```
  to something like:
  ```
  health-dashboard/  # Pipeline health dashboard (observability)
  ```
  And add a line like:
  > **Frontend:** The user-facing frontend application lives in [`hoopstat-haus-frontend`](https://github.com/efischer19/hoopstat-haus-frontend).

- **Grep verification:** Run:
  ```bash
  grep -r "frontend-app" --include="*.md" --include="*.yml" --include="*.yaml" --include="*.tf" --include="*.py" .
  ```
  Every hit should either be removed or updated.

- **Prerequisites:** This ticket depends on Ticket 05 (frontend code removed) and Ticket 06 (cross-repo deployment working). It should be the last PR merged in the epic, ensuring all prior tickets are complete and the system is stable before updating documentation.

- Consider also updating the `mkdocs.yml` navigation if it references any frontend-specific documentation pages.
