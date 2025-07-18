# Example Calculator App

A demonstration application showcasing local development dependency management in the Hoopstat Haus monorepo.

## Purpose

This application demonstrates:

- Local path dependencies using Poetry
- Hot reloading during shared library development
- Integration between apps and shared libraries
- Development workflow best practices

## Features

- Basic arithmetic calculations using the `example-math-utils` shared library
- Interactive calculator mode
- Demonstration of complex calculations using multiple library functions

## Dependencies

This application uses the following local shared library:

- `example-math-utils` (path: `../../libs/example-math-utils`, develop: true)

The `develop = true` flag enables hot reloading, meaning changes to the shared library are immediately available without reinstalling.

## Usage

### Setup

```bash
cd apps/example-calculator-app
poetry install
```

### Running the Application

```bash
# Basic mode - demonstrates calculations
poetry run start

# Interactive mode - allows manual calculations
poetry run python -m app.main --interactive
```

### Development

```bash
# Run tests
poetry run test

# Run linting
poetry run lint

# Format code
poetry run format
```

## Local Development Workflow

This app demonstrates the local development dependency workflow:

1. **Library Changes**: Modify code in `libs/example-math-utils/example_math_utils/calculator.py`
2. **Hot Reloading**: Run the app again to see changes immediately
3. **No Reinstall**: The `develop = true` flag means no `poetry install` needed

### Example: Adding a New Function

1. Add a new function to `libs/example-math-utils/example_math_utils/calculator.py`:
   ```python
   def subtract(a: float, b: float) -> float:
       """Subtract the second number from the first."""
       return a - b
   ```

2. Update the library's `__init__.py` to export it:
   ```python
   from .calculator import add, multiply, divide, subtract
   __all__ = ["add", "multiply", "divide", "subtract"]
   ```

3. Use it in this app's `app/main.py`:
   ```python
   from example_math_utils import subtract
   print(f"10 - 3 = {subtract(10, 3)}")
   ```

4. Run the app immediately to see the new function work:
   ```bash
   poetry run start
   ```

No reinstallation or dependency updates required!

## Configuration Details

The local dependency is configured in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.12"
example-math-utils = {path = "../../libs/example-math-utils", develop = true}
```

Key aspects:
- `path`: Relative path to the shared library
- `develop = true`: Enables hot reloading and editable installs
- No version specification needed for local development

## Testing

The application includes tests that verify:
- Correct integration with the shared library
- Expected calculation outputs
- Error handling for edge cases

Run tests with:
```bash
poetry run pytest
```

## Version History

- `0.1.0`: Initial release demonstrating local dependency management