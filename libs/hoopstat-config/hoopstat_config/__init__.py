"""
hoopstat-config

Standardized configuration management library for Hoopstat Haus applications
"""

__version__ = "0.1.0"

# Public API exports
from .config_field import ConfigField
from .config_manager import ConfigManager, config_field
from .exceptions import ConfigFileError, ConfigValidationError
from .loaders import load_config_file

__all__ = [
    "ConfigManager",
    "ConfigField",
    "config_field",
    "ConfigValidationError",
    "ConfigFileError",
    "load_config_file",
]
