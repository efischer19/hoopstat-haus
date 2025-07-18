"""Tests for the main module."""

from app.main import greet, main, calculate_stats


def test_greet_default():
    """Test greet function with default parameter."""
    result = greet()
    assert result == "Hello, World! Welcome to Hoopstat Haus!"


def test_greet_with_name():
    """Test greet function with custom name."""
    result = greet("Alice")
    assert result == "Hello, Alice! Welcome to Hoopstat Haus!"


def test_greet_empty_string():
    """Test greet function with empty string."""
    result = greet("")
    assert result == "Hello, ! Welcome to Hoopstat Haus!"


def test_calculate_stats():
    """Test calculate_stats function using shared library."""
    result = calculate_stats(10, 5)
    assert result["sum"] == 15
    assert result["average"] == 7.5
    assert result["inputs"] == [10, 5]


def test_main_runs_without_error(capsys):
    """Test that main function runs without error and produces output."""
    main()
    captured = capsys.readouterr()
    assert "Hello, World! Welcome to Hoopstat Haus!" in captured.out
    assert "This is a deployable web application." in captured.out
    assert "Sample calculation:" in captured.out
