"""Tests for the main CLI module."""

from click.testing import CliRunner

from app.main import cli


class TestCLI:
    """Test cases for the CLI interface."""

    def test_cli_help(self):
        """Test that CLI shows help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Silver layer processing pipeline" in result.output

    def test_process_help(self):
        """Test that process command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process Bronze layer data" in result.output

    def test_status_help(self):
        """Test that status command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Check the status" in result.output

    def test_debug_flag(self):
        """Test that debug flag is accepted."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--debug", "status"])
        assert result.exit_code == 0

    def test_dry_run_flag(self):
        """Test that dry-run flag works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process", "--dry-run"])
        assert result.exit_code == 0
