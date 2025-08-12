# Local Development Dependency Management Guide

This guide explains how to efficiently develop with shared libraries in the Hoopstat Haus monorepo using Poetry's local path dependencies with hot reloading.

## Overview

The Hoopstat Haus monorepo supports seamless local development between applications and shared libraries using Poetry's local path dependencies. This enables:

- **Hot reloading**: Library changes are immediately available in consuming applications
- **No reinstalls**: No need to reinstall packages when developing locally
- **Efficient workflow**: Rapid iteration and testing across multiple components

## Quick Start

### 1. Add a Local Dependency

In your application's `pyproject.toml`, add the shared library as a local path dependency:

```toml
[tool.poetry.dependencies]
python = "^3.12"
your-shared-lib = {path = "../../libs/your-shared-lib", develop = true}
```

### 2. Install Dependencies

```bash
cd apps/your-app
poetry install
```

### 3. Use the Library

```python
# In your application code
from your_shared_lib import some_function

result = some_function(data)
```

### 4. Develop with Hot Reloading

1. Modify code in `libs/your-shared-lib/`
2. Run your app: `poetry run start`
3. Changes are immediately available!

## Configuration Details

### Local Path Dependency Syntax

```toml
library-name = {path = "../../libs/library-name", develop = true}
```

**Key components:**
- `path`: Relative path from app to library
- `develop = true`: Enables editable installs and hot reloading

### Path Resolution Examples

```bash
# From apps/web-dashboard/ to libs/auth-utils/
auth-utils = {path = "../../libs/auth-utils", develop = true}

# From apps/data-pipeline/ to libs/basketball-stats/
basketball-stats = {path = "../../libs/basketball-stats", develop = true}
```

### Optional Version Constraints

For production stability, you can add version constraints:

```toml
# Development with version constraint
my-lib = {path = "../../libs/my-lib", version = "^1.0.0", develop = true}

# Production with exact version pinning
my-lib = {path = "../../libs/my-lib", version = "=1.2.3"}
```

## Development Workflow

### Creating a New Shared Library

1. **Create from template:**
   ```bash
   cp -r templates/python-lib-template libs/your-new-lib
   cd libs/your-new-lib
   ```

2. **Customize the library:**
   - Update `pyproject.toml` with correct name and description
   - Rename template directories and files
   - Implement your library functions

3. **Install and test:**
   ```bash
   poetry install
   poetry run pytest
   ```

### Adding Library to Application

1. **Add dependency to app:**
   ```toml
   # In apps/your-app/pyproject.toml
   your-new-lib = {path = "../../libs/your-new-lib", develop = true}
   ```

2. **Install in app:**
   ```bash
   cd apps/your-app
   poetry lock  # Update lock file
   poetry install
   ```

3. **Use in application:**
   ```python
   from your_new_lib import your_function
   ```

### Hot Reloading Development Cycle

```bash
# 1. Make changes to shared library
vim libs/my-lib/my_lib/module.py

# 2. Test library directly (optional)
cd libs/my-lib
poetry run pytest

# 3. Test in consuming application immediately
cd apps/my-app
poetry run start  # Changes are live!

# 4. Run app tests
poetry run test
```

## Best Practices

### 1. Library Development

- **Keep libraries focused**: Each library should have a single, clear purpose
- **Use semantic versioning**: Bump versions appropriately for breaking changes
- **Test thoroughly**: Libraries should have comprehensive test coverage
- **Document well**: Clear documentation and type hints for all public APIs

### 2. Dependency Management

- **Use `develop = true` for active development**: Enables hot reloading
- **Consider version constraints for production**: Pin versions for stability
- **Minimize circular dependencies**: Keep dependency graphs simple
- **Group related functionality**: Don't create too many small libraries

### 3. Development Workflow

- **Test library changes in isolation first**: Run library tests before testing in apps
- **Use relative imports carefully**: Ensure imports work both locally and when installed
- **Keep lock files updated**: Run `poetry lock` when adding new dependencies
- **Document breaking changes**: Clearly communicate API changes to app developers

## Common Patterns

### Pattern 1: Utility Library

```toml
# libs/data-utils/pyproject.toml
[tool.poetry]
name = "data-utils"
version = "0.1.0"
description = "Common data processing utilities"

# apps/data-pipeline/pyproject.toml
[tool.poetry.dependencies]
data-utils = {path = "../../libs/data-utils", develop = true}
```

### Pattern 2: API Client Library

```toml
# libs/nba-api-client/pyproject.toml
[tool.poetry]
name = "nba-api-client"
version = "1.0.0"
description = "NBA API client library"

# apps/stats-collector/pyproject.toml
[tool.poetry.dependencies]
nba-api-client = {path = "../../libs/nba-api-client", version = "^1.0.0", develop = true}
```

### Pattern 3: Multiple Libraries

```toml
# apps/web-dashboard/pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
auth-utils = {path = "../../libs/auth-utils", develop = true}
basketball-stats = {path = "../../libs/basketball-stats", develop = true}
data-visualization = {path = "../../libs/data-visualization", develop = true}
```

## Troubleshooting

### Issue: "Package not found" Errors

**Symptoms:** Import errors or Poetry can't find the library

**Solutions:**
1. Verify the path is correct:
   ```bash
   ls ../../libs/your-lib/pyproject.toml
   ```

2. Ensure the library has a valid `pyproject.toml`
3. Check that the package name matches between library and dependency declaration

### Issue: Changes Not Reflected

**Symptoms:** Library changes don't appear in the application

**Solutions:**
1. Ensure `develop = true` is set in the dependency
2. Restart Python processes/development servers
3. Check for cached imports in long-running processes

### Issue: Version Conflicts

**Symptoms:** Poetry resolver conflicts when adding dependencies

**Solutions:**
1. Use compatible version ranges: `^1.0.0` instead of exact versions
2. Update all related libraries to compatible versions
3. Consider using version overrides for development

### Issue: Circular Dependencies

**Symptoms:** Library A depends on Library B which depends on Library A

**Solutions:**
1. Extract common functionality to a third library
2. Restructure to eliminate circular dependencies
3. Use dependency injection patterns

## Integration with CI/CD

### Testing Shared Libraries

```yaml
# .github/workflows/test-libraries.yml
- name: Test shared libraries
  run: |
    for lib in libs/*/; do
      cd "$lib"
      poetry install
      poetry run pytest
      cd ../..
    done
```

### Testing Applications with Local Dependencies

```yaml
# .github/workflows/test-apps.yml
- name: Test applications
  run: |
    for app in apps/*/; do
      cd "$app"
      poetry install
      poetry run test
      cd ../..
    done
```

## Related Documentation

- [Shared Library Versioning Guide](SHARED_LIBRARY_VERSIONING.md)
- [Development Philosophy](../meta/DEVELOPMENT_PHILOSOPHY.md)
- [ADR-003: Poetry Dependencies](../meta/adr/ADR-003-poetry_deps.md)
- [ADR-016: Shared Library Versioning](../meta/adr/ADR-016-shared_library_versioning.md)

## Examples

See working examples in the repository:

- **Library Example**: `libs/example-math-utils/`
- **Application Example**: `apps/example-calculator-app/`

These demonstrate the complete workflow from library creation to application integration with hot reloading.