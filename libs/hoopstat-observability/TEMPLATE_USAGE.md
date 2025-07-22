# Python Library Template Usage Guide

This template provides a standardized structure for creating new shared libraries in the Hoopstat Haus project.

## How to Use This Template

1. **Copy the template directory**:
   ```bash
   cp -r templates/python-lib-template libs/your-new-library
   ```

2. **Replace template variables**:
   Replace all instances of the following variables with your actual values:
   - `{{LIBRARY_NAME}}`: The name of your library (e.g., `data_processing`)
   - `{{MODULE_NAME}}`: The main module name (e.g., `processors`)
   - `{{LIBRARY_DESCRIPTION}}`: A brief description of your library
   - `{{PURPOSE_DESCRIPTION}}`: A detailed description of the library's purpose

   You can use find/replace in your editor or use this bash command:
   ```bash
   cd libs/your-new-library
   find . -type f -name "*.py" -o -name "*.md" -o -name "*.toml" | xargs sed -i 's/{{LIBRARY_NAME}}/your_library_name/g'
   find . -type f -name "*.py" -o -name "*.md" -o -name "*.toml" | xargs sed -i 's/{{MODULE_NAME}}/your_module_name/g'
   # etc.
   ```

3. **Rename template files**:
   - Rename the `{{LIBRARY_NAME}}` directory to your actual library name
   - Rename `{{LIBRARY_NAME}}/{{MODULE_NAME}}.py` to your actual module name
   - Rename `tests/test_{{MODULE_NAME}}.py` to match your module name

4. **Install dependencies**:
   ```bash
   cd libs/your-new-library
   poetry install
   ```

5. **Customize the code**:
   - Replace the example `example_function` with your actual library functions
   - Update the imports in `__init__.py`
   - Update the test cases to match your functions
   - Update the README with your library's specific documentation

6. **Validate the setup**:
   ```bash
   # Run tests
   poetry run pytest
   
   # Run linting
   poetry run ruff check .
   
   # Format code
   poetry run black .
   ```

## What's Included

- **`pyproject.toml`**: Complete Poetry configuration with:
  - Standard dependencies for Python 3.12
  - Development tools: pytest, ruff, black, pytest-cov
  - Ruff configuration following ADR-005
  - Black configuration following ADR-005
  - Pytest configuration following ADR-004
  - Coverage reporting setup

- **Package Structure**:
  - Proper Python package with `__init__.py`
  - Example module with documented functions
  - Type hints and comprehensive docstrings
  - Public API exports

- **Testing**:
  - Comprehensive test suite using pytest
  - Example test patterns for different scenarios
  - Error handling test cases

- **Documentation**:
  - README template with standard sections
  - API documentation examples
  - Development setup instructions

- **Development Tools**:
  - `.gitignore` with Python-specific exclusions
  - Pre-configured linting and formatting tools

## Standards Followed

This template follows the project's established standards:
- **ADR-005**: Ruff for linting, Black for formatting
- **ADR-004**: pytest for testing
- **ADR-002**: Python 3.12
- Development Philosophy: Code for humans first, simplicity, automated testing