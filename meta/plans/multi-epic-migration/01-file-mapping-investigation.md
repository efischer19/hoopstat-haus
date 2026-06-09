# feat: Create file-to-repo mapping document

## What do you want to build?

A comprehensive markdown document that maps every folder and file in the current hoopstat-haus monorepo to its intended destination repository. This is the foundational planning artifact that all subsequent migration work depends on.

The document should categorize each item as one of:
- **blueprint-repo-blueprints** — language-agnostic template content
- **static-js-app-blueprint** — frontend template content
- **python-project-blueprint** — Python monorepo template content
- **python-aws-data-blueprint** — Python + AWS template content
- **hoopstat-data** — product-specific data pipeline content
- **hoopstat-app** — product-specific frontend content
- **Discard** — content that doesn't migrate (build artifacts, repo-specific config)
- **Multiple** — content that belongs in more than one repo (with notes on adaptation)

## Acceptance Criteria

- [ ] Every top-level directory in hoopstat-haus is accounted for
- [ ] Every file in the root directory is accounted for
- [ ] For directories with mixed content (e.g., `meta/adr/`), individual files or categories are mapped
- [ ] Each mapping includes a brief note explaining the rationale (copy vs. adapt vs. rewrite)
- [ ] The document distinguishes between "copy as-is" and "adapt/generalize" for template repos
- [ ] Items that belong in multiple repos have clear notes on what changes per destination
- [ ] The mapping is organized in a table format for easy scanning
- [ ] The document is placed at `meta/plans/multi-epic-migration/file-mapping.md`

## Implementation Notes (Optional)

Key decisions to make during this investigation:

- **`meta/adr/`**: Most ADRs are hoopstat-specific (e.g., ADR-013 NBA API, ADR-031 Bronze file granularity) and belong in `hoopstat-data`. General ADRs (e.g., ADR-001 Use ADRs, ADR-003 Use Poetry) should be adapted for blueprint repos. ADR-042 (this migration) stays in hoopstat-haus as historical record.
- **`meta/DEVELOPMENT_PHILOSOPHY.md`**: This is core blueprint-repo-blueprints content, copied as-is to all derived repos.
- **`.github/workflows/`**: Each workflow maps to a specific repo. Some (like `ci.yml`) will be generalized for blueprints.
- **`libs/`**: All libraries move to `hoopstat-data`. Blueprint repos get empty `libs/` scaffolding.
- **`apps/`**: All apps move to `hoopstat-data`. Blueprint repos get example app scaffolding.
- **`frontend-app/`**: Moves to `hoopstat-app`. Template version goes in `static-js-app-blueprint`.
- **`infrastructure/`**: Moves to `hoopstat-data`. Terraform scaffolding goes in `python-aws-data-blueprint`.
- **`repomix.config.json`**: Lives in all repos (per issue description).
- **`templates/`**: The Python app/lib templates move to `python-project-blueprint`.

This ticket blocks all other migration work. Take time to be thorough — mistakes here propagate to every subsequent epic.
