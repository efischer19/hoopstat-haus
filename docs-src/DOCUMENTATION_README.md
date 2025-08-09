# Automated Documentation Generation

This directory contains the automated documentation generation system for Hoopstat Haus shared libraries.

## Overview

The documentation system automatically generates API documentation from docstrings in shared libraries and builds a static website using MkDocs. This ensures that documentation stays up-to-date with code changes and provides a centralized location for discovering and understanding shared library functionality.

## Features

- **Automatic API Documentation**: Extracts docstrings from all shared libraries in `/libs/`
- **Usage Examples**: Includes examples from docstring content
- **Type Hints**: Displays function signatures with type annotations
- **Search Functionality**: Full-text search across all documentation
- **Mobile-Friendly**: Responsive design that works on all devices
- **GitHub Integration**: Automatically updates documentation on library changes

## Structure

```
docs-src/               # Source documentation files
├── index.md           # Main documentation page
├── libraries/         # Generated library documentation
│   ├── index.md      # Libraries overview
│   └── *.md          # Individual library docs (auto-generated)
├── *.md              # Copied from /docs/ directory
└── DEVELOPMENT_PHILOSOPHY.md  # Copied from /meta/

mkdocs.yml             # MkDocs configuration
docs-requirements.txt  # Python dependencies for docs
site/                  # Built documentation (ignored by git)
```

## Usage

### Building Documentation Locally

1. Install dependencies:
   ```bash
   pip install -r docs-requirements.txt
   ```

2. Generate and build documentation:
   ```bash
   ./scripts/build-docs.sh
   ```

3. Serve documentation locally:
   ```bash
   mkdocs serve
   ```

   The documentation will be available at http://localhost:8000

### Scripts

- **`scripts/generate-docs.py`**: Extracts docstrings and generates library documentation
- **`scripts/build-docs.sh`**: Complete build process (generate + build)
- **`scripts/check-docs.sh`**: Validates documentation completeness

### Automatic Updates

Documentation is automatically updated when:

- Code changes in any shared library (`libs/**`)
- Documentation source changes (`docs-src/**`)
- Documentation configuration changes (`mkdocs.yml`)
- Documentation scripts change (`scripts/generate-docs.py`, `scripts/build-docs.sh`)

The GitHub Actions workflow:
1. Builds documentation on every PR to validate changes
2. Deploys documentation to GitHub Pages on main branch pushes

## Adding Documentation for New Libraries

When you create a new shared library:

1. Ensure your library has comprehensive docstrings following Google style:
   ```python
   def my_function(param: str) -> bool:
       """
       Brief description of the function.
       
       Longer description if needed.
       
       Args:
           param: Description of the parameter.
           
       Returns:
           Description of the return value.
           
       Example:
           >>> my_function("test")
           True
       """
   ```

2. Run the documentation generation:
   ```bash
   ./scripts/build-docs.sh
   ```

Documentation will be automatically generated and included in the next build.

## Best Practices

### Writing Good Docstrings

- Use Google-style docstrings for consistency
- Include type hints in function signatures
- Provide usage examples in docstrings
- Document all parameters and return values
- Explain any exceptions that may be raised

### Example Good Docstring

```python
def process_data(data: List[Dict[str, Any]], validate: bool = True) -> pd.DataFrame:
    """
    Process raw basketball data into a standardized DataFrame.
    
    This function takes raw basketball statistics data and converts it into
    a pandas DataFrame with standardized column names and data types.
    
    Args:
        data: List of dictionaries containing raw basketball statistics.
            Each dictionary should have keys for player name, team, and stats.
        validate: Whether to validate data integrity before processing.
            Defaults to True.
    
    Returns:
        A pandas DataFrame with standardized basketball statistics.
        Columns include: player_name, team, points, rebounds, assists.
    
    Raises:
        ValueError: If data validation fails and validate=True.
        KeyError: If required data fields are missing.
    
    Example:
        >>> raw_data = [{"name": "LeBron James", "team": "LAL", "pts": 25}]
        >>> df = process_data(raw_data)
        >>> df.columns.tolist()
        ['player_name', 'team', 'points']
    """
```

## Troubleshooting

### Documentation Not Generating

1. Check that your library has an `__init__.py` file
2. Ensure docstrings follow Google style format
3. Run `./scripts/check-docs.sh` to validate completeness
4. Check the build output for any error messages

### Missing Examples

Examples are automatically extracted from docstrings that contain:
- Lines starting with `Example:` or `Examples:`
- Code blocks using `>>>` format

### Build Failures

Common issues:
- Missing dependencies: Install with `pip install -r docs-requirements.txt`
- Python import errors: Ensure libraries can be imported
- Markdown syntax errors: Check generated `.md` files

## Configuration

The documentation system is configured through:

- **`mkdocs.yml`**: Main MkDocs configuration
- **`scripts/generate-docs.py`**: API documentation extraction logic
- **`.github/workflows/documentation.yml`**: CI/CD automation

To customize the documentation appearance or behavior, modify these configuration files.