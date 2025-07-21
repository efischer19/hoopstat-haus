"""Tests for the ConfigManager class."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import validator

from hoopstat_config import ConfigManager, ConfigValidationError, config_field


class TestConfigManager:
    """Test ConfigManager functionality."""

    def setup_method(self):
        """Clean up environment before each test."""
        self.original_env = {}
        test_vars = ["TEST_DEBUG", "TEST_PORT", "TEST_DB_URL", "TEST_SECRET"]
        for var in test_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def teardown_method(self):
        """Restore environment after each test."""
        # Clean up test variables
        test_vars = ["TEST_DEBUG", "TEST_PORT", "TEST_DB_URL", "TEST_SECRET"]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

        # Restore original values
        for var, value in self.original_env.items():
            os.environ[var] = value

    def test_basic_configuration_with_defaults(self):
        """Test basic configuration with default values."""

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            port: int = config_field(default=8000, env_var="TEST_PORT")
            database_url: str = config_field(env_var="TEST_DB_URL")

        # This should fail because database_url is required
        with pytest.raises(ConfigValidationError):
            AppConfig.load()

    def test_configuration_with_override_values(self):
        """Test configuration with override values."""

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            port: int = config_field(default=8000, env_var="TEST_PORT")
            database_url: str = config_field(env_var="TEST_DB_URL")

        config = AppConfig.load(
            override_values={"database_url": "postgresql://localhost/test"}
        )

        assert config.debug is False
        assert config.port == 8000
        assert config.database_url == "postgresql://localhost/test"

        sources = config.get_field_sources()
        assert sources["debug"] == "default"
        assert sources["port"] == "default"
        assert sources["database_url"] == "override"

    def test_configuration_with_environment_variables(self):
        """Test configuration loading from environment variables."""

        # Set environment variables
        os.environ["TEST_DEBUG"] = "true"
        os.environ["TEST_PORT"] = "3000"
        os.environ["TEST_DB_URL"] = "postgresql://localhost/myapp"

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            port: int = config_field(default=8000, env_var="TEST_PORT")
            database_url: str = config_field(env_var="TEST_DB_URL")

        config = AppConfig.load()

        assert config.debug is True
        assert config.port == 3000
        assert config.database_url == "postgresql://localhost/myapp"

        sources = config.get_field_sources()
        assert sources["debug"] == "environment"
        assert sources["port"] == "environment"
        assert sources["database_url"] == "environment"

    def test_configuration_from_json_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "debug": True,
            "port": 3000,
            "database_url": "postgresql://localhost/filetest",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:

            class AppConfig(ConfigManager):
                debug: bool = config_field(default=False, env_var="TEST_DEBUG")
                port: int = config_field(default=8000, env_var="TEST_PORT")
                database_url: str = config_field(env_var="TEST_DB_URL")

            config = AppConfig.load(config_file=config_file)

            assert config.debug is True
            assert config.port == 3000
            assert config.database_url == "postgresql://localhost/filetest"

            sources = config.get_field_sources()
            assert sources["debug"] == "file"
            assert sources["port"] == "file"
            assert sources["database_url"] == "file"

        finally:
            Path(config_file).unlink()

    def test_configuration_precedence(self):
        """Test configuration precedence: defaults < file < env < override."""
        config_data = {
            "debug": True,
            "port": 3000,
            "database_url": "postgresql://localhost/filetest",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        # Set environment variables that will override some file values
        os.environ["TEST_PORT"] = "4000"

        try:

            class AppConfig(ConfigManager):
                debug: bool = config_field(default=False, env_var="TEST_DEBUG")
                port: int = config_field(default=8000, env_var="TEST_PORT")
                database_url: str = config_field(env_var="TEST_DB_URL")
                secret: str = config_field(
                    default="default_secret", env_var="TEST_SECRET"
                )

            config = AppConfig.load(
                config_file=config_file, override_values={"secret": "override_secret"}
            )

            # debug comes from file (True)
            assert config.debug is True
            # port comes from environment (4000) - overrides file
            assert config.port == 4000
            # database_url comes from file
            assert config.database_url == "postgresql://localhost/filetest"
            # secret comes from override - overrides default
            assert config.secret == "override_secret"

            sources = config.get_field_sources()
            assert sources["debug"] == "file"
            assert sources["port"] == "environment"
            assert sources["database_url"] == "file"
            assert sources["secret"] == "override"

        finally:
            Path(config_file).unlink()

    def test_configuration_summary(self):
        """Test configuration summary functionality."""

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            port: int = config_field(default=8000, env_var="TEST_PORT")
            password: str = config_field(default="secret", env_var="TEST_PASSWORD")

        config = AppConfig.load()
        summary = config.get_config_summary()

        assert "Configuration Summary for AppConfig:" in summary
        assert "debug: False (source: default)" in summary
        assert "port: 8000 (source: default)" in summary
        assert "password: *** (source: default)" in summary  # Should be masked

    def test_get_env_vars(self):
        """Test getting environment variable mappings."""

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            port: int = config_field(default=8000, env_var="TEST_PORT")
            no_env: str = config_field(default="test")  # No env var

        config = AppConfig.load()
        env_vars = config.get_env_vars()

        expected = {"debug": "TEST_DEBUG", "port": "TEST_PORT"}
        assert env_vars == expected

    def test_load_from_file_only(self):
        """Test loading from file without environment variable processing."""
        config_data = {
            "debug": True,
            "port": 3000,
            "database_url": "postgresql://localhost/filetest",
        }

        # Set environment variable that should be ignored
        os.environ["TEST_DEBUG"] = "false"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:

            class AppConfig(ConfigManager):
                debug: bool = config_field(default=False, env_var="TEST_DEBUG")
                port: int = config_field(default=8000, env_var="TEST_PORT")
                database_url: str = config_field(env_var="TEST_DB_URL")

            config = AppConfig.load_from_file(config_file)

            # Should use file values, not environment
            assert config.debug is True  # From file, not env var
            assert config.port == 3000
            assert config.database_url == "postgresql://localhost/filetest"

            sources = config.get_field_sources()
            assert sources["debug"] == "file"
            assert sources["port"] == "file"
            assert sources["database_url"] == "file"

        finally:
            Path(config_file).unlink()

    def test_validation_error_handling(self):
        """Test custom validation error handling."""

        class AppConfig(ConfigManager):
            port: int = config_field(default=8000, env_var="TEST_PORT")

            @validator("port")
            def validate_port(cls, v):
                if not 1 <= v <= 65535:
                    raise ValueError("Port must be between 1 and 65535")
                return v

        # Test with invalid override value
        with pytest.raises(ConfigValidationError) as exc_info:
            AppConfig.load(override_values={"port": 100000})

        assert "Configuration validation failed" in str(exc_info.value)
        assert len(exc_info.value.errors) > 0
        assert exc_info.value.errors[0]["field"] == "port"

    def test_optional_fields(self):
        """Test optional configuration fields."""

        class AppConfig(ConfigManager):
            debug: bool = config_field(default=False, env_var="TEST_DEBUG")
            redis_url: str | None = config_field(default=None, env_var="TEST_REDIS_URL")

        config = AppConfig.load()

        assert config.debug is False
        assert config.redis_url is None

        # Test with environment variable set
        os.environ["TEST_REDIS_URL"] = "redis://localhost:6379"
        config = AppConfig.load()

        assert config.redis_url == "redis://localhost:6379"
