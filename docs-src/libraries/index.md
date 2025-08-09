# Shared Libraries Overview

This section provides detailed documentation for all shared libraries in the Hoopstat Haus monorepo. Each library is designed to be reusable across multiple applications while following our development principles.

## Library Categories

### Configuration & Setup
- **hoopstat-config**: Standardized configuration management with type safety and validation

### Data Processing
- **hoopstat-data**: Core data processing utilities for basketball statistics
- **ingestion**: Data ingestion utilities for external data sources

### Testing & Development
- **hoopstat-e2e-testing**: End-to-end testing framework and utilities
- **hoopstat-mock-data**: Mock data generation for testing scenarios
- **example-math-utils**: Example library demonstrating best practices

### Observability
- **hoopstat-observability**: Logging, monitoring, and observability utilities

## Usage Patterns

All shared libraries follow consistent patterns:

### Installation
Add to your application's `pyproject.toml`:
```toml
[tool.poetry.dependencies]
library-name = {path = "../libs/library-name", develop = true}
```

### Import Style
```python
from library_name import ClassName, function_name
```

### Error Handling
All libraries use consistent exception patterns and provide clear error messages.

### Documentation
Each library includes:
- Comprehensive docstrings with Google-style formatting
- Usage examples in docstrings
- Type hints for all public APIs
- Integration examples in documentation

## Best Practices

When using shared libraries:

1. **Pin Versions**: Use semantic versioning to pin library versions in production
2. **Follow Examples**: Use the patterns shown in library documentation
3. **Handle Errors**: Implement proper error handling for library exceptions
4. **Test Integration**: Write tests for your usage of shared libraries
5. **Stay Updated**: Monitor library changes and update dependencies regularly

## Development Guidelines

When contributing to shared libraries:

1. **Maintain Backward Compatibility**: Follow semantic versioning principles
2. **Write Tests**: All public APIs must have comprehensive tests
3. **Document Everything**: Include docstrings with examples for all public functions
4. **Follow Standards**: Use consistent code style and patterns across libraries
5. **Consider Dependencies**: Minimize external dependencies and document requirements