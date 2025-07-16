# Hoopstat Common Library

Shared utilities for Hoopstat Haus Python applications.

## Overview

This library provides common utilities that are shared across multiple Python applications in the Hoopstat Haus monorepo. It follows the DRY principle by centralizing reusable code that would otherwise be duplicated across applications.

## Features

### Performance Monitoring

Provides decorator and context manager utilities for automatic performance monitoring and structured JSON logging according to ADR-015.

```python
from hoopstat_common.performance import performance_monitor, performance_context

# Using the decorator
@performance_monitor(job_name="data_processing")
def process_data():
    # Your data processing logic
    return {"records_processed": 1500, "status": "success"}

# Using the context manager
with performance_context("batch_job") as ctx:
    for batch in data_batches:
        process_batch(batch)
        ctx["records_processed"] += len(batch)
```

## Installation

This library is intended to be used as a local dependency in other Python applications within the Hoopstat Haus monorepo.

In your application's `pyproject.toml`, add:

```toml
[tool.poetry.dependencies]
hoopstat-common = {path = "../../libs/hoopstat-common", develop = true}
```

Then run:

```bash
poetry install
```

## Development

### Running Tests

```bash
poetry install
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
poetry run ruff check .
```

## Adding New Utilities

When adding new shared utilities:

1. Create the module in `hoopstat_common/`
2. Add comprehensive tests in `tests/`
3. Update this README with usage examples
4. Consider backward compatibility for existing consumers

## Versioning

This library follows semantic versioning. Breaking changes will increment the major version and require coordination with consuming applications.