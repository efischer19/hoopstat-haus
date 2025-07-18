"""Tests for the calculator module."""

import pytest

from example_math_utils.calculator import add, divide, multiply, subtract


class TestCalculator:
    """Test cases for calculator functions."""

    def test_add_positive_numbers(self):
        """Test adding positive numbers."""
        result = add(2, 3)
        assert result == 5.0

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        result = add(-2, -3)
        assert result == -5.0

    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        result = add(-2, 3)
        assert result == 1.0

    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        result = multiply(4, 5)
        assert result == 20.0

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = multiply(5, 0)
        assert result == 0.0

    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        result = divide(10, 2)
        assert result == 5.0

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)

    def test_divide_zero_by_number(self):
        """Test dividing zero by a number."""
        result = divide(0, 5)
        assert result == 0.0

    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        result = subtract(10, 3)
        assert result == 7.0

    def test_subtract_negative_result(self):
        """Test subtraction that results in negative number."""
        result = subtract(3, 10)
        assert result == -7.0

    def test_subtract_same_numbers(self):
        """Test subtracting same numbers."""
        result = subtract(5, 5)
        assert result == 0.0


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_complex_calculation(self):
        """Test a complex calculation using multiple functions."""
        # Calculate: (2 + 3) * 4 / 2 - 1 = 9
        step1 = add(2, 3)  # 5
        step2 = multiply(step1, 4)  # 20
        step3 = divide(step2, 2)  # 10
        result = subtract(step3, 1)  # 9
        assert result == 9.0
