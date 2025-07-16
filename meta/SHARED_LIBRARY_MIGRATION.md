# Migration Guide: Using Shared Libraries

This guide helps migrate existing Python applications to use the shared `hoopstat-common` library instead of duplicated code.

## Overview

The shared library approach (ADR-016) provides common utilities that prevent code duplication across applications. The primary shared utility is performance monitoring from ADR-015.

## Migration Steps

### 1. Add Shared Library Dependency

In your application's `pyproject.toml`, add the shared library as a dependency:

```toml
[tool.poetry.dependencies]
python = "^3.12"
hoopstat-common = {path = "../../libs/hoopstat-common", develop = true}
```

Note: Adjust the path based on your application's location relative to `libs/hoopstat-common`.

### 2. Update Dependencies

Run Poetry to install the new dependency:

```bash
poetry lock
poetry install
```

### 3. Update Imports

Replace local performance monitoring imports with shared library imports:

**Before:**
```python
from app.performance import performance_monitor, performance_context
```

**After:**
```python
from hoopstat_common.performance import performance_monitor, performance_context
```

### 4. Update Test Imports

Update test files that import performance utilities:

**Before:**
```python
from app.performance import (
    _extract_records_processed,
    _log_performance_metrics,
    performance_context,
    performance_monitor,
)
```

**After:**
```python
from hoopstat_common.performance import (
    _extract_records_processed,
    _log_performance_metrics,
    performance_context,
    performance_monitor,
)
```

### 5. Update Test Mocks

Update any mock patches in tests:

**Before:**
```python
@patch("app.performance.time.strftime")
```

**After:**
```python
@patch("hoopstat_common.performance.time.strftime")
```

### 6. Remove Duplicated Code

After verifying that tests pass with the shared library:

1. Remove the local `performance.py` file
2. Remove performance-related tests if they duplicate shared library tests
3. Update documentation and README files

### 7. Verify Migration

Run your application's test suite to ensure everything works:

```bash
poetry run pytest
```

## Benefits After Migration

- **Reduced Code Duplication:** Performance monitoring code exists in one place
- **Easier Maintenance:** Updates to performance monitoring affect all applications
- **Consistent Behavior:** All applications use the same performance monitoring logic
- **Better Testing:** Shared utilities have their own comprehensive test suite

## Troubleshooting

### Import Errors

If you get import errors, verify:
1. The shared library path in `pyproject.toml` is correct
2. You've run `poetry lock` and `poetry install`
3. The shared library is properly installed in your virtual environment

### Test Failures

If tests fail after migration:
1. Check that all imports have been updated
2. Verify that mock patches point to the correct module
3. Ensure test data and expectations match shared library behavior

### Path Issues

If the relative path to the shared library doesn't work:
1. Verify your application's location in the monorepo
2. Use `develop = true` to enable live changes during development
3. Consider using absolute paths if needed for your deployment

## Getting Help

- Review ADR-016 for the shared library strategy
- Check the `hoopstat-common` README for usage examples
- Look at the updated `python-app-template` for reference implementation