"""Tests for the configuration field functionality."""

import os

import pytest

from hoopstat_config.config_field import ConfigField, config_field
from hoopstat_config.exceptions import ConfigEnvironmentError


class TestConfigField:
    """Test ConfigField class functionality."""

    def test_create_field_with_defaults(self):
        """Test creating a field with default values."""
        field = ConfigField(default="test", env_var="TEST_VAR")

        assert field.default == "test"
        assert field.env_var == "TEST_VAR"
        assert field.description is None

    def test_create_field_with_description(self):
        """Test creating a field with description."""
        field = ConfigField(
            default=42, env_var="PORT", description="Server port number"
        )

        assert field.default == 42
        assert field.env_var == "PORT"
        assert field.description == "Server port number"

    def test_create_required_field(self):
        """Test creating a required field (no default)."""
        field = ConfigField(env_var="REQUIRED_VAR")

        assert field.default is ...
        assert field.env_var == "REQUIRED_VAR"


class TestEnvironmentVariableHandling:
    """Test environment variable parsing and type conversion."""

    def setup_method(self):
        """Clean up environment variables before each test."""
        # Store original values to restore later
        self.original_env = {}
        test_vars = ["TEST_STR", "TEST_INT", "TEST_FLOAT", "TEST_BOOL", "TEST_LIST"]
        for var in test_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def teardown_method(self):
        """Restore original environment variables after each test."""
        # Clean up test variables
        test_vars = ["TEST_STR", "TEST_INT", "TEST_FLOAT", "TEST_BOOL", "TEST_LIST"]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

        # Restore original values
        for var, value in self.original_env.items():
            os.environ[var] = value

    def test_string_conversion(self):
        """Test string environment variable conversion."""
        os.environ["TEST_STR"] = "hello world"
        field = ConfigField(env_var="TEST_STR")

        result = field.get_env_value(str)
        assert result == "hello world"

    def test_integer_conversion(self):
        """Test integer environment variable conversion."""
        os.environ["TEST_INT"] = "42"
        field = ConfigField(env_var="TEST_INT")

        result = field.get_env_value(int)
        assert result == 42

    def test_float_conversion(self):
        """Test float environment variable conversion."""
        os.environ["TEST_FLOAT"] = "3.14"
        field = ConfigField(env_var="TEST_FLOAT")

        result = field.get_env_value(float)
        assert result == 3.14

    def test_boolean_conversion_true_values(self):
        """Test boolean conversion for true values."""
        field = ConfigField(env_var="TEST_BOOL")
        true_values = ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON", "enabled"]

        for value in true_values:
            os.environ["TEST_BOOL"] = value
            result = field.get_env_value(bool)
            assert result is True, f"Failed for value: {value}"

    def test_boolean_conversion_false_values(self):
        """Test boolean conversion for false values."""
        field = ConfigField(env_var="TEST_BOOL")
        false_values = [
            "false",
            "False",
            "FALSE",
            "0",
            "no",
            "NO",
            "off",
            "OFF",
            "disabled",
        ]

        for value in false_values:
            os.environ["TEST_BOOL"] = value
            result = field.get_env_value(bool)
            assert result is False, f"Failed for value: {value}"

    def test_boolean_conversion_invalid(self):
        """Test boolean conversion with invalid values."""
        os.environ["TEST_BOOL"] = "maybe"
        field = ConfigField(env_var="TEST_BOOL")

        with pytest.raises(ConfigEnvironmentError) as exc_info:
            field.get_env_value(bool)

        assert "Cannot convert 'maybe' to boolean" in str(exc_info.value)
        assert exc_info.value.env_var == "TEST_BOOL"
        assert exc_info.value.env_value == "maybe"

    def test_list_conversion(self):
        """Test list environment variable conversion."""
        os.environ["TEST_LIST"] = "item1,item2,item3"
        field = ConfigField(env_var="TEST_LIST")

        result = field.get_env_value(list[str])
        assert result == ["item1", "item2", "item3"]

    def test_list_conversion_with_spaces(self):
        """Test list conversion with whitespace handling."""
        os.environ["TEST_LIST"] = " item1 , item2 , item3 "
        field = ConfigField(env_var="TEST_LIST")

        result = field.get_env_value(list[str])
        assert result == ["item1", "item2", "item3"]

    def test_list_conversion_integers(self):
        """Test list conversion with integer elements."""
        os.environ["TEST_LIST"] = "1,2,3"
        field = ConfigField(env_var="TEST_LIST")

        result = field.get_env_value(list[int])
        assert result == [1, 2, 3]

    def test_optional_type_conversion(self):
        """Test conversion with Optional types."""
        os.environ["TEST_STR"] = "test_value"
        field = ConfigField(env_var="TEST_STR")

        result = field.get_env_value(str | None)
        assert result == "test_value"

    def test_env_var_not_set(self):
        """Test behavior when environment variable is not set."""
        field = ConfigField(env_var="NONEXISTENT_VAR")

        result = field.get_env_value(str)
        assert result is None

    def test_no_env_var_specified(self):
        """Test behavior when no environment variable is specified."""
        field = ConfigField(default="test")

        result = field.get_env_value(str)
        assert result is None

    def test_invalid_type_conversion(self):
        """Test error handling for invalid type conversions."""
        os.environ["TEST_INT"] = "not_a_number"
        field = ConfigField(env_var="TEST_INT")

        with pytest.raises(ConfigEnvironmentError) as exc_info:
            field.get_env_value(int)

        assert "Failed to convert environment variable to int" in str(exc_info.value)
        assert exc_info.value.env_var == "TEST_INT"
        assert exc_info.value.env_value == "not_a_number"


class TestConfigFieldFactory:
    """Test the config_field factory function."""

    def test_create_field_with_factory(self):
        """Test creating a field using the factory function."""
        field = config_field(default="test", env_var="TEST_VAR")

        # Should return a Pydantic Field object
        assert hasattr(field, "default")
        assert field.default == "test"

    def test_factory_with_description(self):
        """Test factory function with description."""
        field = config_field(default=8080, env_var="PORT", description="Server port")

        assert field.default == 8080
        assert field.description == "Server port"
