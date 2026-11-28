# feat: Archive hoopstat-haus repository with final README

## What do you want to build?

Archive the hoopstat-haus repository on GitHub, replacing the README with a redirect notice pointing to the new repositories. This is the final step of the migration.

## Acceptance Criteria

- [ ] Root `README.md` is replaced with an archive notice that includes:
  - A clear statement that this repository is archived
  - Links to `hoopstat-data` and `hoopstat-app` as the successor repositories
  - Links to the blueprint template repos for anyone interested in the template system
  - A brief history of what this repo was and why it was split
  - The date of archival
- [ ] All open issues are closed with a comment redirecting to the appropriate new repo
- [ ] All open PRs are closed with a comment explaining the archival
- [ ] The repository description on GitHub is updated to "[ARCHIVED] See hoopstat-data and hoopstat-app"
- [ ] The repository is set to "Archived" status on GitHub (read-only)
- [ ] GitHub Pages (if enabled) is disabled or redirects to the new site
- [ ] The repository topics are updated to include "archived"

## Implementation Notes (Optional)

**Pre-archival checklist:**
Before archiving, verify one final time:
1. ✅ hoopstat-data is operational (pipeline running, CI green)
2. ✅ hoopstat-app is operational (frontend deployed, accessible)
3. ✅ hoopstat.haus DNS points to the new infrastructure
4. ✅ All secrets and tokens are removed (ticket 30)
5. ✅ All AWS infrastructure is torn down (ticket 29)
6. ✅ No scheduled workflows are active

**Archive README template:**
```markdown
# hoopstat-haus [ARCHIVED]

> This repository has been archived as of [DATE]. The project has been split into
> dedicated repositories as part of a planned migration.

## Successor Repositories

| Repository | Description |
|-----------|-------------|
| [hoopstat-data](https://github.com/efischer19/hoopstat-data) | NBA data pipeline, shared libraries, and AWS infrastructure |
| [hoopstat-app](https://github.com/efischer19/hoopstat-app) | Frontend analytics dashboard at hoopstat.haus |

## Template Repositories

This project's patterns have been generalized into reusable templates:
- [blueprint-repo-blueprints](...)
- [static-js-app-blueprint](...)
- [python-project-blueprint](...)
- [python-aws-data-blueprint](...)

## History

[Brief description of what this repo was and the migration rationale]
```

This is an irreversible action — once archived, the repo becomes read-only. Make absolutely sure all migration and deployment steps are complete before proceeding.
