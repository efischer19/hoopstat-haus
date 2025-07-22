#!/usr/bin/env python3
"""
Demo script showing hoopstat-config functionality.
"""

import json
import os
import tempfile
from pathlib import Path

from hoopstat_config import ConfigManager, config_field


class DatabaseConfig(ConfigManager):
    """Example database configuration."""

    host: str = config_field(default="localhost", env_var="DB_HOST")
    port: int = config_field(default=5432, env_var="DB_PORT")
    username: str = config_field(env_var="DB_USER")
    password: str = config_field(env_var="DB_PASSWORD")
    database: str = config_field(default="myapp", env_var="DB_NAME")


class AppConfig(ConfigManager):
    """Example application configuration."""

    debug: bool = config_field(default=False, env_var="DEBUG")
    port: int = config_field(default=8000, env_var="PORT")
    redis_url: str | None = config_field(default=None, env_var="REDIS_URL")


def demo_basic_usage():
    """Demonstrate basic configuration usage."""
    print("=" * 60)
    print("DEMO: Basic Configuration Usage")
    print("=" * 60)

    # Set some environment variables
    os.environ["DEBUG"] = "true"
    os.environ["PORT"] = "3000"

    try:
        config = AppConfig.load()
        print("✓ Configuration loaded successfully!")
        print(f"  Debug mode: {config.debug}")
        print(f"  Server port: {config.port}")
        print(f"  Redis URL: {config.redis_url}")

        print("\nField sources:")
        sources = config.get_field_sources()
        for field, source in sources.items():
            print(f"  {field}: {source}")

    except Exception as e:
        print(f"✗ Configuration failed: {e}")
    finally:
        # Clean up
        for var in ["DEBUG", "PORT"]:
            if var in os.environ:
                del os.environ[var]


def demo_config_file():
    """Demonstrate configuration file loading."""
    print("\n" + "=" * 60)
    print("DEMO: Configuration File Loading")
    print("=" * 60)

    # Create a temporary config file
    config_data = {"debug": True, "port": 4000, "redis_url": "redis://localhost:6379"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    try:
        config = AppConfig.load(config_file=config_file)
        print(f"✓ Configuration loaded from file: {config_file}")
        print(f"  Debug mode: {config.debug}")
        print(f"  Server port: {config.port}")
        print(f"  Redis URL: {config.redis_url}")

        print("\nField sources:")
        sources = config.get_field_sources()
        for field, source in sources.items():
            print(f"  {field}: {source}")

    except Exception as e:
        print(f"✗ Configuration failed: {e}")
    finally:
        # Clean up
        Path(config_file).unlink()


def demo_precedence():
    """Demonstrate configuration precedence."""
    print("\n" + "=" * 60)
    print("DEMO: Configuration Precedence")
    print("=" * 60)

    # Create config file
    config_data = {
        "debug": False,
        "port": 4000,
        "redis_url": "redis://config-file:6379",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    # Set environment variable (should override file)
    os.environ["PORT"] = "5000"

    try:
        config = AppConfig.load(
            config_file=config_file,
            override_values={"redis_url": "redis://override:6379"},
        )

        print("Configuration with precedence:")
        print(f"  Debug mode: {config.debug} (from file)")
        print(f"  Server port: {config.port} (from environment)")
        print(f"  Redis URL: {config.redis_url} (from override)")

        print("\nField sources:")
        sources = config.get_field_sources()
        for field, source in sources.items():
            print(f"  {field}: {source}")

    except Exception as e:
        print(f"✗ Configuration failed: {e}")
    finally:
        # Clean up
        Path(config_file).unlink()
        if "PORT" in os.environ:
            del os.environ["PORT"]


def demo_validation_error():
    """Demonstrate validation error handling."""
    print("\n" + "=" * 60)
    print("DEMO: Validation Error Handling")
    print("=" * 60)

    try:
        # Try to load config without required fields
        DatabaseConfig.load()
        print("✗ This shouldn't happen - required fields should cause validation error")
    except Exception as e:
        print("✓ Validation error caught successfully!")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")


def demo_config_summary():
    """Demonstrate configuration summary."""
    print("\n" + "=" * 60)
    print("DEMO: Configuration Summary")
    print("=" * 60)

    # Set up a complete configuration
    os.environ["DEBUG"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379"

    try:
        config = AppConfig.load()
        print("Configuration summary:")
        print(config.get_config_summary())

        print("\nEnvironment variable mappings:")
        env_vars = config.get_env_vars()
        for field, env_var in env_vars.items():
            print(f"  {field} -> {env_var}")

    except Exception as e:
        print(f"✗ Configuration failed: {e}")
    finally:
        # Clean up
        for var in ["DEBUG", "REDIS_URL"]:
            if var in os.environ:
                del os.environ[var]


if __name__ == "__main__":
    print("Hoopstat Configuration Management Demo")
    print("======================================")

    demo_basic_usage()
    demo_config_file()
    demo_precedence()
    demo_validation_error()
    demo_config_summary()

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
