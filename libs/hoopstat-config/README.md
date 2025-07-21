# Hoopstat Configuration Management

A standardized configuration management library that provides type-safe configuration handling with support for multiple formats and validation.

## Purpose

This library provides a consistent approach to configuration management across all Hoopstat Haus applications, supporting:

- Environment variable handling with automatic type conversion
- Configuration file parsing for multiple formats (JSON, YAML, TOML)
- Layered configuration with clear precedence rules
- Type-safe configuration with runtime validation
- Clear error messages and debugging support
- Integration with Python's logging system

## Quick Start

### Basic Usage

```python
from hoopstat_config import ConfigManager, ConfigField
from typing import Optional

class AppConfig(ConfigManager):
    # Basic configuration with defaults
    debug: bool = ConfigField(default=False, env_var="DEBUG")
    port: int = ConfigField(default=8000, env_var="PORT")
    database_url: str = ConfigField(env_var="DATABASE_URL")
    
    # Optional configuration
    redis_url: Optional[str] = ConfigField(default=None, env_var="REDIS_URL")

# Load configuration
config = AppConfig.load()
print(f"Server running on port {config.port}")
```

### Configuration Files

```python
# Load from configuration file
config = AppConfig.load_from_file("config.yaml")

# Load with layered configuration (file + environment variables)
config = AppConfig.load(config_file="config.yaml")
```

### Configuration File Formats

**YAML (config.yaml)**
```yaml
debug: true
port: 3000
database_url: "postgresql://localhost/myapp"
```

**TOML (config.toml)**
```toml
debug = true
port = 3000
database_url = "postgresql://localhost/myapp"
```

**JSON (config.json)**
```json
{
    "debug": true,
    "port": 3000,
    "database_url": "postgresql://localhost/myapp"
}
```

## Features

### Type Safety and Validation

```python
from hoopstat_config import ConfigManager, ConfigField
from pydantic import validator

class DatabaseConfig(ConfigManager):
    host: str = ConfigField(env_var="DB_HOST")
    port: int = ConfigField(default=5432, env_var="DB_PORT")
    username: str = ConfigField(env_var="DB_USER")
    password: str = ConfigField(env_var="DB_PASSWORD")
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
```

### Environment Variable Type Conversion

The library automatically converts environment variables to the correct Python types:

```bash
export DEBUG=true          # → bool
export PORT=8000           # → int  
export TIMEOUT=30.5        # → float
export TAGS=tag1,tag2,tag3 # → List[str]
```

### Configuration Layering

Configuration values are resolved in this order (later values override earlier ones):

1. **Default values** defined in the class
2. **Configuration file** values (if provided)
3. **Environment variables** (if defined)

### Error Handling

```python
try:
    config = AppConfig.load()
except ConfigValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    # e.errors contains detailed validation information
    for error in e.errors:
        logger.error(f"Field '{error['field']}': {error['message']}")
```

## Advanced Usage

### Custom Validation

```python
from hoopstat_config import ConfigManager, ConfigField, ConfigValidationError
from typing import List

class AdvancedConfig(ConfigManager):
    allowed_hosts: List[str] = ConfigField(
        default=["localhost"],
        env_var="ALLOWED_HOSTS",
        description="Comma-separated list of allowed hosts"
    )
    
    @validator('allowed_hosts', pre=True)
    def parse_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
```

### Configuration Debugging

```python
# Get configuration summary
config = AppConfig.load()
print(config.get_config_summary())

# Get field sources (where each value came from)
sources = config.get_field_sources()
print(f"Port value came from: {sources['port']}")  # 'default', 'file', or 'environment'
```

## Development

### Setup

```bash
cd libs/hoopstat-config
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

To use this library in an application:

```toml
# In apps/your-app/pyproject.toml
[tool.poetry.dependencies]
python = "^3.12"
hoopstat-config = {path = "../../libs/hoopstat-config", develop = true}
```

## Version History

- `0.1.0`: Initial release with basic configuration management features