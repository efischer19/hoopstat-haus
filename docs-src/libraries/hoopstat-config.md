# hoopstat-config

**Version:** 0.1.0

## Description

hoopstat-config

Standardized configuration management library for Hoopstat Haus applications

## Installation

Add to your application's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
hoopstat-config = {path = "../libs/hoopstat-config", develop = true}
```

## Usage

```python
from hoopstat_config import ConfigManager, ConfigField, config_field, ConfigValidationError, ConfigFileError, load_config_file
```

## API Reference

### Classes

#### ConfigManager

Base class for type-safe configuration management.

This class provides a foundation for creating configuration classes that:
- Load from multiple sources (defaults, files, environment variables)
- Provide type safety and validation
- Support multiple file formats
- Give clear error messages
- Track configuration sources for debugging

**Methods:**

- `load(cls: Any, config_file: Any, override_values: Any) -> T`
  - Load configuration from multiple sources with precedence rules.
- `load_from_file(cls: Any, config_file: str) -> T`
  - Load configuration from a file only (no environment variables).
- `get_field_sources(self) -> Any`
  - Get information about where each field value came from.
- `get_config_summary(self) -> str`
  - Get a human-readable summary of the configuration.
- `get_env_vars(self) -> Any`
  - Get environment variable names for all fields that support them.

#### ConfigValidationError

Raised when configuration validation fails.

This exception provides detailed information about validation failures
to help developers quickly identify and fix configuration issues.

#### ConfigFileError

Raised when configuration file loading or parsing fails.

This exception is used for file system errors, parsing errors,
and other file-related issues during configuration loading.

#### ConfigEnvironmentError

Raised when environment variable processing fails.

This exception is used when environment variables cannot be parsed
or converted to the expected types.

#### ConfigField

Defines a configuration field with support for environment variables and validation.

This class provides a declarative way to define configuration fields with:
- Default values
- Environment variable mapping
- Type conversion
- Documentation
- Validation

**Methods:**

- `get_env_value(self, field_type: Any) -> Any`
  - Get and convert value from environment variable.

### Functions

#### config_field

```python
config_field(default: Any, env_var: Any, description: Any) -> Any
```

Create a configuration field with environment variable support.

This function creates a Pydantic field with additional metadata
for environment variable handling.

Args:
    default: Default value for the field.
    env_var: Environment variable name to read the value from.
    description: Human-readable description of the field.
    **kwargs: Additional arguments passed to pydantic.Field()

Returns:
    Pydantic Field for use in model definitions.

#### load

```python
load(cls: Any, config_file: Any, override_values: Any) -> T
```

Load configuration from multiple sources with precedence rules.

Configuration sources (in order of precedence, later overrides earlier):
1. Class defaults
2. Configuration file (if provided)
3. Environment variables
4. Override values (if provided)

Args:
    config_file: Optional path to configuration file
    override_values: Optional dictionary of values to override

Returns:
    Configured instance of the class

Raises:
    ConfigValidationError: If configuration validation fails
    ConfigFileError: If configuration file cannot be loaded

#### load_from_file

```python
load_from_file(cls: Any, config_file: str) -> T
```

Load configuration from a file only (no environment variables).

Args:
    config_file: Path to configuration file

Returns:
    Configured instance of the class

Raises:
    ConfigValidationError: If configuration validation fails
    ConfigFileError: If configuration file cannot be loaded

#### get_field_sources

```python
get_field_sources(self) -> Any
```

Get information about where each field value came from.

Returns:
    Dictionary mapping field names to source types:
    - 'default': From class default value
    - 'file': From configuration file
    - 'environment': From environment variable
    - 'override': From override values

#### get_config_summary

```python
get_config_summary(self) -> str
```

Get a human-readable summary of the configuration.

Returns:
    Formatted string showing all configuration values and their sources

#### get_env_vars

```python
get_env_vars(self) -> Any
```

Get environment variable names for all fields that support them.

Returns:
    Dictionary mapping field names to environment variable names

#### config_field

```python
config_field(default: Any, env_var: Any, description: Any) -> Any
```

Create a configuration field with environment variable support.

This is a convenience function that creates a ConfigField and returns
its Pydantic field for use in class definitions.

Args:
    default: Default value for the field.
    env_var: Environment variable name to read the value from.
    description: Human-readable description of the field.
    **kwargs: Additional arguments passed to pydantic.Field()

Returns:
    Pydantic Field object for use in model definitions.

#### get_env_value

```python
get_env_value(self, field_type: Any) -> Any
```

Get and convert value from environment variable.

Args:
    field_type: The expected type for the field value.

Returns:
    Converted value from environment variable, or None if not set.

Raises:
    ConfigEnvironmentError: If environment variable exists but cannot be
        converted.

#### load_config_file

```python
load_config_file(file_path: str) -> Any
```

Load configuration from a file, auto-detecting format from extension.

Supported formats:
- JSON (.json)
- YAML (.yaml, .yml) - requires PyYAML
- TOML (.toml) - requires tomli (Python < 3.11) or uses stdlib tomllib
  (Python >= 3.11)

Args:
    file_path: Path to the configuration file.

Returns:
    Dictionary containing the parsed configuration.

Raises:
    ConfigFileError: If the file cannot be read or parsed.

#### get_supported_formats

```python
get_supported_formats() -> Any
```

Get information about supported configuration file formats.

Returns:
    Dictionary mapping format names to availability status.
