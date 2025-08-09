# Hoopstat Haus Shared Libraries Documentation

Welcome to the official documentation for Hoopstat Haus shared Python libraries. This documentation provides comprehensive API references, usage examples, and best practices for using our shared libraries across different applications.

## Overview

The Hoopstat Haus project uses a monorepo structure with shared libraries located in the `/libs/` directory. These libraries provide common functionality that can be reused across multiple applications, following the DRY (Don't Repeat Yourself) principle.

## Available Libraries

### Core Libraries

- **[hoopstat-config](libraries/hoopstat-config.md)** - Standardized configuration management
- **[hoopstat-data](libraries/hoopstat-data.md)** - Data processing utilities for basketball statistics
- **[hoopstat-observability](libraries/hoopstat-observability.md)** - Logging and monitoring utilities

### Utility Libraries

- **[example-math-utils](libraries/example-math-utils.md)** - Example math utilities (demonstration)
- **[hoopstat-mock-data](libraries/hoopstat-mock-data.md)** - Mock data generation for testing
- **[hoopstat-e2e-testing](libraries/hoopstat-e2e-testing.md)** - End-to-end testing utilities
- **[ingestion](libraries/ingestion.md)** - Data ingestion utilities

## Quick Start

To use any shared library in your application:

1. Add it to your `pyproject.toml` dependencies:
   ```toml
   [tool.poetry.dependencies]
   hoopstat-config = {path = "../libs/hoopstat-config", develop = true}
   ```

2. Import and use in your code:
   ```python
   from hoopstat_config import ConfigManager
   
   config = ConfigManager()
   ```

## Development Philosophy

All shared libraries follow the [Hoopstat Haus Development Philosophy](DEVELOPMENT_PHILOSOPHY.md):

- **Code is for Humans First** - Clear, readable, well-documented code
- **Favor Simplicity** - Static-first design with minimal complexity
- **Confidence Through Testing** - Comprehensive automated tests
- **Clean Commit History** - Atomic commits with descriptive messages

## Contributing

For information on contributing to shared libraries, see:

- [Contributing Guidelines](CONTRIBUTING.md)
- [Shared Library Versioning](SHARED_LIBRARY_VERSIONING.md)
- [Local Development Dependencies](LOCAL_DEVELOPMENT_DEPENDENCIES.md)

## Getting Help

- Check the API documentation for specific library usage
- Review usage examples in the library documentation
- See integration tests for real-world usage patterns
- Refer to the development documentation for advanced topics