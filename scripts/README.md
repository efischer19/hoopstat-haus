# Development Scripts

This directory contains scripts to help with local development and quality assurance.

## local-ci-check.sh

Runs the same quality checks that CI runs for Python projects (apps and libs).

### Usage

```bash
# From repository root
./scripts/local-ci-check.sh apps/your-app
./scripts/local-ci-check.sh libs/your-lib
```

### What it checks

1. **Dependencies**: Installs project dependencies via Poetry
2. **Formatting**: Checks code formatting with `ruff format --check`
3. **Linting**: Runs linting checks with `ruff check`
4. **Tests**: Runs the test suite with `pytest`

### When to use

- Before committing changes to Python projects
- Before opening a pull request
- When debugging CI failures locally
- As part of your development workflow

This script ensures your code will pass CI checks, reducing review cycles and maintaining code quality.