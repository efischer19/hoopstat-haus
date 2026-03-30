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
- [ ] ADR for "Use Python 3.12+" is present (adapted from hoopstat-haus ADR-002)
- [ ] ADR for "Use Poetry for Dependency Management" is present (adapted from ADR-003)

## Implementation Notes (Optional)

This is where the Python ecosystem choices from hoopstat-haus get generalized. Key ADRs to adapt:
- ADR-002 (Python 3.12+) → General-purpose ADR for this template
- ADR-003 (Poetry) → General-purpose ADR for this template
- ADR-004 (pytest) → General-purpose ADR for this template
- ADR-005 (Ruff) → General-purpose ADR for this template (note: hoopstat-haus uses Ruff for both linting AND formatting now, not Black separately)
- ADR-008 (Monorepo with /apps) → General-purpose ADR for this template

Do NOT include Docker, AWS, or infrastructure concerns here — those belong in `python-aws-data-blueprint`. This template should be usable for any Python project, whether it's a CLI tool, library, web app, or data pipeline.
