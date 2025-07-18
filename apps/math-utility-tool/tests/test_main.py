"""Tests for the math utility tool."""

import sys
from unittest.mock import patch

import pytest

from app.main import calculate_from_args, main, run_batch_calculations


class TestCalculateFromArgs:
    """Test the calculate_from_args function."""

    def test_add_operation(self, capsys):
        """Test addition operation."""
        calculate_from_args(["add", "5", "3"])
        captured = capsys.readouterr()
        assert "5.0 add 3.0 = 8.0" in captured.out

    def test_subtract_operation(self, capsys):
        """Test subtraction operation."""
        calculate_from_args(["subtract", "10", "4"])
        captured = capsys.readouterr()
        assert "10.0 subtract 4.0 = 6.0" in captured.out

    def test_multiply_operation(self, capsys):
        """Test multiplication operation."""
        calculate_from_args(["multiply", "6", "7"])
        captured = capsys.readouterr()
        assert "6.0 multiply 7.0 = 42.0" in captured.out

    def test_divide_operation(self, capsys):
        """Test division operation."""
        calculate_from_args(["divide", "20", "4"])
        captured = capsys.readouterr()
        assert "20.0 divide 4.0 = 5.0" in captured.out

    def test_divide_by_zero_exits(self, capsys):
        """Test that division by zero causes exit."""
        with pytest.raises(SystemExit) as exc_info:
            calculate_from_args(["divide", "10", "0"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Cannot divide by zero" in captured.out

    def test_invalid_operation_exits(self, capsys):
        """Test that invalid operation causes exit."""
        with pytest.raises(SystemExit) as exc_info:
            calculate_from_args(["invalid", "5", "3"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Unknown operation 'invalid'" in captured.out

    def test_invalid_numbers_exit(self, capsys):
        """Test that invalid numbers cause exit."""
        with pytest.raises(SystemExit) as exc_info:
            calculate_from_args(["add", "not_a_number", "3"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Please provide valid numbers" in captured.out

    def test_insufficient_args_exits(self, capsys):
        """Test that insufficient arguments cause exit."""
        with pytest.raises(SystemExit) as exc_info:
            calculate_from_args(["add", "5"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage: poetry run calculate" in captured.out


class TestRunBatchCalculations:
    """Test the run_batch_calculations function."""

    def test_batch_calculations_output(self, capsys):
        """Test that batch calculations produce expected output."""
        run_batch_calculations()
        captured = capsys.readouterr()

        assert "Math Utility Tool - Batch Calculations" in captured.out
        assert "10 add 5 = 15" in captured.out
        assert "20 subtract 8 = 12" in captured.out
        assert "6 multiply 7 = 42" in captured.out
        assert "100 divide 4 = 25.0" in captured.out


class TestMain:
    """Test the main function."""

    @patch.object(sys, "argv", ["script"])
    def test_main_no_args_runs_batch(self, capsys):
        """Test that main with no args runs batch calculations."""
        main()
        captured = capsys.readouterr()

        assert "Math Utility Tool" in captured.out
        assert "No arguments provided" in captured.out
        assert "Running batch calculations" in captured.out
        assert "10 add 5 = 15" in captured.out

    @patch.object(sys, "argv", ["script", "add", "2", "3"])
    def test_main_with_args_calculates(self, capsys):
        """Test that main with args performs calculation."""
        main()
        captured = capsys.readouterr()
        assert "2.0 add 3.0 = 5.0" in captured.out
