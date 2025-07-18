# Python Application Template

This is the standard Python application template for Hoopstat Haus projects. It demonstrates the recommended project structure, tooling, and development workflow.

## Features

- **Python 3.12+** runtime
- **Poetry** for dependency management  
- **pytest** for testing
- **Ruff** for linting
- **Black** for code formatting
- **Docker** with multi-stage builds
- Standard project scripts

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Docker (optional)

### Setup

1. Copy this template to create a new project:
   ```bash
   cp -r templates/python-app-template apps/your-new-app
   cd apps/your-new-app
   ```

2. Update project details in `pyproject.toml`:
   - Change `name` from "python-app-template" to your app name
   - Update `description` and `authors`
   - Update the package name in `packages` field

3. Install dependencies:
   ```bash
   poetry install
   ```

## Development Workflow

### Local Shared Library Dependencies

For applications that need to use shared libraries from the monorepo, add them as local path dependencies in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.12"
# Add shared libraries as local path dependencies
your-shared-lib = {path = "../../libs/your-shared-lib", develop = true}
```

The `develop = true` flag enables hot reloading, meaning changes to the shared library are immediately available without reinstalling. This enables efficient local development workflow:

1. Modify shared library code in `libs/your-shared-lib/`
2. Run your application immediately with `poetry run start` 
3. Changes are automatically reflected without reinstalling

### Standard Scripts

The template provides standard scripts that should be used across all Python projects:

```bash
# Run the application
poetry run start

# Run tests
poetry run test

# Run linting
poetry run lint

# Format code
poetry run format
```

### Development Commands

```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Run the application directly
poetry run python -m app.main

# Run tests with coverage
poetry run pytest --cov=app

# Fix linting issues automatically
poetry run ruff check --fix .

# Check if code is formatted correctly
poetry run black --check .
```

### Docker Usage

```bash
# Build development image
docker build --target development -t your-app:dev .

# Build production image
docker build --target production -t your-app:prod .

# Run development container
docker run -it your-app:dev

# Run production container
docker run your-app:prod
```

## Project Structure

```
your-app/
├── app/                    # Application source code
│   ├── __init__.py
│   ├── main.py            # Main application entry point
│   ├── performance.py     # Performance monitoring utilities
│   └── scripts.py         # Development scripts
├── tests/                 # Test files
│   ├── __init__.py
│   ├── test_main.py
│   └── test_performance.py
├── Dockerfile             # Multi-stage Docker configuration
├── pyproject.toml         # Poetry configuration and dependencies
└── README.md             # This file
```

## Configuration

### Poetry (pyproject.toml)

The `pyproject.toml` file contains all project configuration:
- Dependencies and dev dependencies
- Tool configurations (Ruff, Black, pytest)
- Project metadata
- Build system configuration

### Ruff Linting

Ruff is configured to check for:
- Code style issues (pycodestyle)
- Potential bugs (pyflakes, flake8-bugbear) 
- Import sorting (isort)
- Code modernization (pyupgrade)

### Black Formatting

Black provides opinionated code formatting with minimal configuration:
- Line length: 88 characters
- Target Python version: 3.12

### pytest Testing

pytest is configured with:
- Test discovery in `tests/` directory
- Coverage reporting support
- Strict marker checking

## Performance Monitoring

This template includes built-in performance monitoring utilities for data pipeline instrumentation, following the Hoopstat Haus Logging Strategy (ADR-015-json_logging).

### Using the Performance Monitor Decorator

The `@performance_monitor` decorator automatically logs execution time and record count:

```python
from app.performance import performance_monitor

@performance_monitor(job_name="user_data_sync")
def sync_users():
    # Process data...
    return {"records_processed": 1500, "status": "success"}

@performance_monitor()  # Uses function name as job_name
def process_records():
    # Process data...
    return 250  # Return record count directly
```

### Using the Performance Context Manager

For more dynamic scenarios, use the context manager:

```python
from app.performance import performance_context

with performance_context("data_export") as ctx:
    for batch in get_data_batches():
        process_batch(batch)
        ctx["records_processed"] += len(batch)
```

### Log Output Format

Both utilities log structured JSON following ADR-015-json_logging requirements:

```json
{
  "timestamp": "2025-01-27T14:30:45.123Z",
  "level": "INFO",
  "message": "Data pipeline job completed successfully",
  "job_name": "user_data_sync", 
  "duration_in_seconds": 45.67,
  "records_processed": 1500,
  "status": "success"
}
```

### Supported Return Types

The decorator can extract record counts from:
- Integer return values: `return 250`
- Dict with `records_processed` key: `return {"records_processed": 250}`
- Dict with custom key: Use `records_processed_key` parameter
- Objects with `records_processed` attribute

## Best Practices

1. **Follow the standard scripts**: Always use `poetry run start`, `poetry run test`, etc.
2. **Run linting and formatting**: Before committing, run `poetry run lint` and `poetry run format`
3. **Write tests**: Add tests for new functionality in the `tests/` directory
4. **Use type hints**: Add type hints to function signatures
5. **Document functions**: Add docstrings to public functions and classes
6. **Keep it simple**: Follow the project's development philosophy of simplicity
7. **Monitor data pipelines**: Use performance monitoring utilities for all data processing jobs

## Integration with CI/CD

This template is designed to work seamlessly with GitHub Actions workflows that:
- Install Poetry and dependencies
- Run the standard scripts (`test`, `lint`, `format`)
- Build Docker images
- Deploy applications

The standard scripts ensure consistency across all Python projects in the repository.