"""Tests for the main calculator application module."""

import sys
from unittest.mock import call, patch

import pytest

from app.main import calculate_expression, main


class TestCalculateExpression:
    """Test cases for the calculate_expression function."""

    @patch("builtins.print")
    def test_calculate_expression_basic_output(self, mock_print):
        """Test that calculate_expression produces expected output."""
        calculate_expression()

        # Check that the function prints the expected calculations
        expected_calls = [
            call("Calculator Application - Local Development Demo"),
            call("=" * 50),
            call("\nBasic Arithmetic Examples:"),
            call("2 + 3 = 5"),
            call("4 * 5 = 20"),
            call("20 / 4 = 5.0"),
            call("10 - 3 = 7  <- NEW FUNCTION!"),
            call("\nComplex Calculation: (10 + 5) * 2 / 3"),
            call("Result: 10.0"),
            call("\nThis demonstrates hot reloading of shared libraries!"),
            call(
                "Try modifying libs/example-math-utils/example_math_utils/calculator.py"
            ),
            call("and run this app again to see changes immediately."),
        ]

        mock_print.assert_has_calls(expected_calls)

    @patch("app.main.run_interactive_calculator")
    @patch("builtins.print")
    def test_calculate_expression_interactive_mode(self, mock_print, mock_interactive):
        """Test that interactive mode is triggered with --interactive flag."""
        # Mock sys.argv to include --interactive
        with patch.object(sys, "argv", ["main.py", "--interactive"]):
            calculate_expression()

        # Verify interactive calculator was called
        mock_interactive.assert_called_once()


class TestMain:
    """Test cases for the main function."""

    @patch("app.main.calculate_expression")
    def test_main_calls_calculate_expression(self, mock_calculate):
        """Test that main function calls calculate_expression."""
        main()
        mock_calculate.assert_called_once()


class TestIntegration:
    """Integration tests that verify the app works with the shared library."""

    def test_shared_library_integration(self):
        """Test that the app can import and use the shared library functions."""
        # This test verifies that the import works and basic operations function
        from example_math_utils import add, divide, multiply, subtract

        # Test basic operations work as expected
        assert add(2, 3) == 5.0
        assert multiply(4, 5) == 20.0
        assert divide(20, 4) == 5.0
        assert subtract(10, 3) == 7.0

        # Test that divide by zero raises appropriate error
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
