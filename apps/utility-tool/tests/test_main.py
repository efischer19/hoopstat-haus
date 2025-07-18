"""Tests for the main module."""

from app.main import greet, main, process_numbers


def test_greet_default():
    """Test greet function with default parameter."""
    result = greet()
    assert result == "Hello, World! This is a utility tool!"


def test_greet_with_name():
    """Test greet function with custom name."""
    result = greet("Developer")
    assert result == "Hello, Developer! This is a utility tool!"


def test_process_numbers():
    """Test process_numbers function using shared library."""
    result = process_numbers(1, 2, 3, 4, 5)
    assert result["total"] == 15
    assert result["count"] == 5
    assert result["average"] == 3.0
    assert result["inputs"] == [1, 2, 3, 4, 5]


def test_process_numbers_insufficient():
    """Test process_numbers with insufficient arguments."""
    result = process_numbers(1)
    assert "error" in result
    assert result["error"] == "Need at least 2 numbers"


def test_main_runs_without_error(capsys):
    """Test that main function runs without error and produces output."""
    main()
    captured = capsys.readouterr()
    assert "Hello, Developer! This is a utility tool!" in captured.out
    assert "This is a utility tool (not for deployment)." in captured.out
    assert "Processing numbers:" in captured.out
