# {{LIBRARY_NAME}}

{{LIBRARY_DESCRIPTION}}

## Purpose

{{PURPOSE_DESCRIPTION}}

## Installation

To use this library in your project:

```bash
# If this library is published to PyPI
pip install {{LIBRARY_NAME}}

# If using from the monorepo
from libs.{{LIBRARY_NAME}} import {{MODULE_NAME}}
```

## Usage

```python
from {{LIBRARY_NAME}} import {{MODULE_NAME}}

# Example usage
result = {{MODULE_NAME}}.example_function("hello")
print(result)  # Output: "HELLO"
```

## API Reference

### `{{MODULE_NAME}}` module

#### `example_function(text: str) -> str`
Converts the input text to uppercase.

**Parameters:**
- `text` (str): The input text to convert

**Returns:**
- str: The uppercase version of the input text

**Example:**
```python
result = example_function("hello world")
# Returns: "HELLO WORLD"
```

## Development

This library follows the project's standard development practices:
- Code formatting with Black
- Linting with Ruff  
- Testing with pytest
- Type hints for all public functions

### Setting up for development

1. Install dependencies:
```bash
poetry install
```

2. Run tests:
```bash
poetry run pytest
```

3. Run linting:
```bash
poetry run ruff check .
```

4. Format code:
```bash
poetry run black .
```

## Testing

To run the full test suite:
```bash
poetry run pytest
```

To run tests with coverage:
```bash
poetry run pytest --cov={{LIBRARY_NAME}}
```

## Versioning

This library follows [Semantic Versioning (SemVer)](https://semver.org/):

- **MAJOR**: Breaking changes that require code changes in consuming applications
- **MINOR**: New backward-compatible features  
- **PATCH**: Backward-compatible bug fixes

### Version Management

To update the library version:

```bash
# For bug fixes
poetry version patch    # 1.0.0 → 1.0.1

# For new features
poetry version minor    # 1.0.0 → 1.1.0

# For breaking changes  
poetry version major    # 1.0.0 → 2.0.0
```

See [Shared Library Versioning Guide](../../docs/SHARED_LIBRARY_VERSIONING.md) for detailed versioning guidelines and dependency management.

## Contributing

Please follow the project's development philosophy and guidelines in `meta/DEVELOPMENT_PHILOSOPHY.md`.