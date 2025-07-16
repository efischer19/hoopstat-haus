"""Tests for the main module."""


from app.main import greet, main


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


def test_main_runs_without_error(capsys):
    """Test that main function runs without error and produces output."""
    main()
    captured = capsys.readouterr()
    assert "Hello, World! Welcome to Hoopstat Haus!" in captured.out
    assert "This is a template Python application." in captured.out
    assert "It demonstrates the standard project structure and tooling." in captured.out
