"""
Configuration file loaders for multiple formats (JSON, YAML, TOML).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

from .exceptions import ConfigFileError

# Optional imports with graceful fallbacks
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    # Python 3.11+ has tomllib in stdlib
    import tomllib

    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

logger = logging.getLogger(__name__)


def load_config_file(file_path: str) -> dict[str, Any]:
    """
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
    """
    path = Path(file_path)

    if not path.exists():
        raise ConfigFileError("Configuration file not found", file_path=str(path))

    if not path.is_file():
        raise ConfigFileError("Configuration path is not a file", file_path=str(path))

    try:
        # Determine loader based on file extension
        suffix = path.suffix.lower()

        if suffix == ".json":
            return _load_json(path)
        elif suffix in (".yaml", ".yml"):
            return _load_yaml(path)
        elif suffix == ".toml":
            return _load_toml(path)
        else:
            raise ConfigFileError(
                f"Unsupported file format '{suffix}'. "
                f"Supported formats: .json, .yaml, .yml, .toml",
                file_path=str(path),
            )

    except Exception as e:
        if isinstance(e, ConfigFileError):
            raise

        raise ConfigFileError(
            f"Failed to load configuration file: {e}",
            file_path=str(path),
            original_error=e,
        ) from e


def _load_json(path: Path) -> dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ConfigFileError(
                f"JSON configuration must be an object, got {type(data).__name__}",
                file_path=str(path),
            )

        return data

    except json.JSONDecodeError as e:
        raise ConfigFileError(
            f"Invalid JSON syntax: {e}", file_path=str(path), original_error=e
        ) from e


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load configuration from YAML file."""
    if not YAML_AVAILABLE:
        raise ConfigFileError(
            "PyYAML is required to load YAML configuration files. "
            "Install it with: pip install pyyaml",
            file_path=str(path),
        )

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            # Empty YAML file
            return {}

        if not isinstance(data, dict):
            raise ConfigFileError(
                f"YAML configuration must be a mapping, got {type(data).__name__}",
                file_path=str(path),
            )

        return data

    except yaml.YAMLError as e:
        raise ConfigFileError(
            f"Invalid YAML syntax: {e}", file_path=str(path), original_error=e
        ) from e


def _load_toml(path: Path) -> dict[str, Any]:
    """Load configuration from TOML file."""
    if not TOML_AVAILABLE:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        raise ConfigFileError(
            f"TOML support is not available (Python {python_version})",
            file_path=str(path),
        )

    try:
        with path.open("rb") as f:
            data = tomllib.load(f)

        if not isinstance(data, dict):
            raise ConfigFileError(
                f"TOML configuration must be a table, got {type(data).__name__}",
                file_path=str(path),
            )

        return data

    except Exception as e:
        # tomllib/tomli can raise various exceptions
        raise ConfigFileError(
            f"Invalid TOML syntax: {e}", file_path=str(path), original_error=e
        ) from e


def get_supported_formats() -> dict[str, bool]:
    """
    Get information about supported configuration file formats.

    Returns:
        Dictionary mapping format names to availability status.
    """
    return {
        "json": True,  # Always available (stdlib)
        "yaml": YAML_AVAILABLE,
        "toml": TOML_AVAILABLE,
    }
