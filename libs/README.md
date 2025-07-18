# Shared Libraries Directory

The `/libs` directory contains reusable Python libraries that can be shared across multiple applications in the Hoopstat Haus monorepo.

## Purpose

This directory provides a standardized location for shared Python code components that:
- Implement common functionality needed by multiple applications
- Provide utilities, helpers, and shared business logic
- Maintain consistent interfaces and patterns across the project
- Enable code reuse while avoiding duplication

## Directory Structure

Each library within `/libs` should follow this standard structure:

```
libs/
├── library-name/
│   ├── README.md              # Library documentation
│   ├── pyproject.toml         # Poetry configuration (if standalone)
│   ├── library_name/          # Python package (underscore naming)
│   │   ├── __init__.py
│   │   └── [module files]
│   └── tests/                 # Library-specific tests (if standalone)
│       ├── __init__.py
│       └── test_*.py
└── README.md                  # This file
```

## Naming Conventions

### Library Directory Names
- Use **kebab-case** for library directory names (e.g., `data-utils`, `auth-helpers`)
- Names should be descriptive and indicate the library's purpose
- Avoid abbreviations unless they are widely understood
- Keep names concise but clear

### Python Package Names
- Use **snake_case** for the actual Python package directory (e.g., `data_utils`, `auth_helpers`)
- This follows Python PEP 8 conventions for package names
- The package name should match the library directory name, converted to snake_case

### Examples
- Library: `basketball-stats` → Package: `basketball_stats`
- Library: `data-pipeline-utils` → Package: `data_pipeline_utils`
- Library: `api-clients` → Package: `api_clients`

## Organization Principles

### 1. Single Responsibility
Each library should have a clear, single purpose. Avoid creating large, monolithic libraries that try to do too much.

### 2. Minimal Dependencies
Libraries should have minimal external dependencies to reduce complexity and potential conflicts. When dependencies are needed, they should be clearly documented.

### 3. Clear Interfaces
Libraries should provide clean, well-documented APIs that are easy to understand and use. Follow Python conventions for public vs. private interfaces.

### 4. Self-Contained
Each library should be self-contained and not depend on other libraries in the `/libs` directory unless absolutely necessary. This prevents circular dependencies and coupling.

### 5. Backward Compatibility
When updating libraries, maintain backward compatibility when possible. Use semantic versioning principles for breaking changes.

## Usage Patterns

### Importing from Applications
Applications in the `/apps` directory can import from libraries using relative imports:

```python
# From an app in /apps/my-app/
from libs.data_utils import basketball_stats
from libs.api_clients.nba_client import NBAClient
```

### Development Workflow
1. Create a new directory under `/libs` using kebab-case naming
2. Set up the Python package structure with snake_case naming
3. Add a descriptive README.md for the library
4. Follow the same code quality standards as applications (ruff, black, pytest)
5. Document the library's API and usage examples

## Integration with Applications

Libraries are designed to be imported and used by applications but may also be developed as standalone packages if they need independent testing or deployment.

For libraries that require extensive testing or have complex dependencies, consider adding a `pyproject.toml` file to enable independent development and testing.

## Future Considerations

This structure is designed to grow with the project while maintaining organization and clarity. As the number of libraries increases, we may introduce subcategories or additional organization principles.