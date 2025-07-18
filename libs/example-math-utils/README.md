# Example Math Utils

An example shared library demonstrating local development dependency management in the Hoopstat Haus monorepo.

## Purpose

This library provides basic mathematical utility functions and serves as a working example of:

- Local path dependencies in Poetry
- Hot reloading during development
- Shared library versioning patterns
- Testing patterns for shared libraries

## Functions

### `add(a: float, b: float) -> float`

Add two numbers together.

```python
from example_math_utils import add

result = add(2, 3)  # 5.0
```

### `multiply(a: float, b: float) -> float`

Multiply two numbers together.

```python
from example_math_utils import multiply

result = multiply(4, 5)  # 20.0
```

### `divide(a: float, b: float) -> float`

Divide the first number by the second number.

```python
from example_math_utils import divide

result = divide(10, 2)  # 5.0
```

Raises `ValueError` if divisor is zero.

## Development

This library follows the standard Hoopstat Haus development patterns:

### Setup

```bash
cd libs/example-math-utils
poetry install
```

### Testing

```bash
poetry run pytest
```

### Linting and Formatting

```bash
poetry run ruff check .
poetry run black .
```

## Usage in Applications

To use this library in an application with local path dependencies:

```toml
# In apps/your-app/pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
example-math-utils = {path = "../../libs/example-math-utils", develop = true}
```

The `develop = true` flag enables hot reloading - changes to the library will be immediately available in the consuming application without reinstalling.

## Version History

- `0.1.0`: Initial release with basic mathematical functions