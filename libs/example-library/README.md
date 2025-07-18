# Example Library

This is an example library demonstrating the standard structure and conventions for shared libraries in the Hoopstat Haus project.

## Purpose

This library serves as a template and example for creating new shared libraries. It demonstrates:
- Proper directory structure and naming conventions
- Documentation standards
- Basic Python package setup
- Code organization principles

## Usage

This is an example library and is not intended for production use. Use it as a reference when creating new libraries.

```python
from libs.example_library import utilities

# Example usage
result = utilities.example_function("hello")
print(result)  # Output: "HELLO"
```

## API Reference

### `utilities` module

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

## Testing

To run tests for this library (if it had a standalone pyproject.toml):
```bash
cd libs/example-library
poetry run pytest
```