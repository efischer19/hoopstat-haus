"""Tests for the {{LIBRARY_NAME}} {{MODULE_NAME}} module."""

import pytest

from {{LIBRARY_NAME}}.{{MODULE_NAME}} import example_function


class TestExampleFunction:
    """Test cases for the example_function."""

    def test_basic_conversion(self):
        """Test basic string to uppercase conversion."""
        result = example_function("hello")
        assert result == "HELLO"

    def test_mixed_case(self):
        """Test conversion of mixed case string."""
        result = example_function("Hello World")
        assert result == "HELLO WORLD"

    def test_already_uppercase(self):
        """Test that already uppercase strings remain unchanged."""
        result = example_function("HELLO")
        assert result == "HELLO"

    def test_empty_string(self):
        """Test handling of empty string."""
        result = example_function("")
        assert result == ""

    def test_with_numbers_and_symbols(self):
        """Test string with numbers and symbols."""
        result = example_function("hello123!@#")
        assert result == "HELLO123!@#"

    def test_invalid_input_type(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError, match="Input must be a string"):
            example_function(123)

        with pytest.raises(TypeError, match="Input must be a string"):
            example_function(None)
