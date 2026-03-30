# feat: Python monorepo structure for python-project-blueprint

## What do you want to build?

Flesh out the Python monorepo structure in `python-project-blueprint` with example app and library scaffolding, shared configuration, and the local development tooling that makes the monorepo pattern work smoothly.

## Acceptance Criteria

- [ ] `apps/example-app/` exists with a minimal Python app skeleton: `pyproject.toml`, `app/__init__.py`, `app/main.py`, `tests/`, `README.md`
- [ ] `libs/example-lib/` exists with a minimal Python library skeleton: `pyproject.toml`, `example_lib/__init__.py`, `tests/`, `README.md`
- [ ] The example app declares a path dependency on the example lib in its `pyproject.toml`
- [ ] `templates/python-app-template/` exists with a cookiecutter-style app template (adapted from hoopstat-haus `templates/`)
- [ ] `templates/python-lib-template/` exists with a cookiecutter-style lib template
- [ ] `.pre-commit-config.yaml` is updated with Python-specific hooks: ruff format, ruff check (adapted from hoopstat-haus)
- [ ] `scripts/local-ci-check.sh` is updated to run Python quality checks (format, lint, test) for a given app/lib directory
- [ ] `scripts/setup-local-deps.py` exists to install local dependencies across the monorepo (adapted from hoopstat-haus)
- [ ] Example app and lib both pass `poetry install && poetry run ruff format --check . && poetry run ruff check . && poetry run pytest`
- [ ] `docker-compose.test.yml` stub exists showing how to run tests in containers (optional)

## Implementation Notes (Optional)

Adapt from hoopstat-haus:
- `templates/python-app-template/` and `templates/python-lib-template/` — Generalize, remove hoopstat-specific deps
- `scripts/setup-local-deps.py` — Generalize for any monorepo structure
- `scripts/local-ci-check.sh` — Generalize
- `.pre-commit-config.yaml` — Add ruff hooks targeting Python files

The example app should be truly minimal:
- A Click CLI that prints "Hello from example-app" (demonstrating ADR-022 pattern)
- A single test that verifies the CLI runs without error
- No actual business logic

The example lib should be:
- A single utility function (e.g., `def greet(name: str) -> str`)
- A single test that verifies the function
- Demonstrates the path dependency pattern for monorepo libs

Library naming convention: kebab-case directories, snake_case Python packages (consistent with hoopstat-haus pattern).
