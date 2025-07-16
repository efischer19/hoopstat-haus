"""Tests for the main module."""

from unittest.mock import patch

from app.main import get_health_status, greet, main


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


def test_get_health_status():
    """Test health status function."""
    health = get_health_status()

    assert health["status"] == "healthy"
    assert "timestamp" in health
    assert "app_name" in health
    assert "app_version" in health
    assert "environment" in health
    assert isinstance(health["debug"], bool)


def test_main_runs_without_error(capsys):
    """Test that main function runs without error and produces output."""
    main()
    captured = capsys.readouterr()

    assert "Hello, World! Welcome to Hoopstat Haus!" in captured.out
    assert "This is a template Python application." in captured.out
    assert "It demonstrates the standard project structure and tooling." in captured.out
    assert "Application Health Status:" in captured.out


def test_main_with_settings_override(capsys):
    """Test main function with different settings."""
    with patch("app.config.settings") as mock_settings:
        mock_settings.app_name = "test-app"
        mock_settings.app_version = "1.0.0"
        mock_settings.app_environment = "testing"
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"
        mock_settings.debug = True

        main()
        captured = capsys.readouterr()

        # Should still contain core output
        assert "Hello, World! Welcome to Hoopstat Haus!" in captured.out
