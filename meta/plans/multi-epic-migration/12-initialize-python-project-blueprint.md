# feat: Initialize python-project-blueprint from blueprint-repo-blueprints

## What do you want to build?

Create the `python-project-blueprint` repository using the `blueprint-repo-blueprints` template. This repo will serve as a template for Python monorepo projects, targeting Python 3.12+ with Poetry dependency management. Set up the foundational Python-specific structure.

## Acceptance Criteria

- [ ] Repository `python-project-blueprint` is created from `blueprint-repo-blueprints` template
- [ ] Template repository setting is enabled
- [ ] Root `README.md` is updated to describe this as a Python monorepo template
- [ ] `.gitignore` is updated with Python-specific entries (__pycache__, *.pyc, .venv, dist/, *.egg-info, .mypy_cache, .pytest_cache, .ruff_cache)
- [ ] Top-level directory structure includes: `apps/`, `libs/`, `templates/`, `scripts/`, `testing/`
- [ ] `apps/README.md` explains the apps directory purpose and conventions
- [ ] `libs/README.md` explains the libs directory purpose and conventions
- [ ] `.github/copilot-instructions.md` is updated with Python-specific development workflow (Poetry, ruff, pytest)
- [ ] `.python-version` file specifies 3.12+
- [ ] `.dockerignore` is present with Python-specific Docker ignore rules (adapted from hoopstat-haus)
- [ ] ADR for "Use Python 3.12+" is present (adapted from hoopstat-haus ADR-002)
- [ ] ADR for "Use Poetry for Dependency Management" is present (adapted from ADR-003)
- [ ] All applicable general Python ADRs are present (per file-mapping): ADR-004 (pytest), ADR-005 (Ruff), ADR-006 (Docker), ADR-008 (Monorepo /apps, adapted), ADR-015 (JSON Logging), ADR-016 (Shared Library Versioning, adapted), ADR-021 (Tenacity), ADR-022 (Click CLI), ADR-023 (MkDocs), ADR-029 (Piwheels ARM builds)

## Implementation Notes (Optional)

This is where the Python ecosystem choices from hoopstat-haus get generalized. The file-mapping identifies 12 ADRs that belong here:
- ADR-002 (Python 3.12+), ADR-003 (Poetry), ADR-004 (pytest), ADR-005 (Ruff) — Core tooling
- ADR-006 (Docker Containers) — General containerization pattern (not AWS-specific)
- ADR-008 (Monorepo /apps Structure) — Adapt for single-project focus
- ADR-015 (JSON Logging) — Logging strategy for all Python repos
- ADR-016 (Shared Library Versioning) — Adapt for multi-repo context
- ADR-021 (Tenacity Retry Logic), ADR-022 (Click CLI), ADR-023 (MkDocs) — Library/tool choices
- ADR-029 (Piwheels ARM Builds) — ARM build optimization for Docker

Do NOT include AWS, Terraform, or cloud-specific concerns here — those belong in `python-aws-data-blueprint`. Docker is included as a general containerization practice, but ECR and Lambda-specific Docker patterns are not.
