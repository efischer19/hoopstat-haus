"""Tests for the bronze layer ingestion main module."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from app.main import cli, main


class TestCLI:
    """Test the command line interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that CLI help is displayed correctly."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Bronze layer ingestion pipeline for NBA statistics" in result.output

    def test_cli_debug_option(self):
        """Test that debug option is recognized."""
        result = self.runner.invoke(cli, ["--debug", "--help"])
        assert result.exit_code == 0

    @patch("app.main.get_logger")
    def test_ingest_command(self, mock_logger):
        """Test the ingest command runs successfully."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        result = self.runner.invoke(cli, ["ingest", "--dry-run"])
        assert result.exit_code == 0

    @patch("app.main.get_logger")
    def test_ingest_command_with_season(self, mock_logger):
        """Test the ingest command with custom season."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        result = self.runner.invoke(cli, ["ingest", "--season", "2023-24", "--dry-run"])
        assert result.exit_code == 0

    @patch("app.main.get_logger")
    def test_status_command(self, mock_logger):
        """Test the status command runs successfully."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        result = self.runner.invoke(cli, ["status"])
        assert result.exit_code == 0


class TestMain:
    """Test the main entry point."""

    @patch("app.main.cli")
    def test_main_calls_cli(self, mock_cli):
        """Test that main() calls the CLI."""
        main()
        mock_cli.assert_called_once()

    @patch("sys.argv", ["app.main"])
    @patch("app.main.cli")
    def test_main_as_script(self, mock_cli):
        """Test running as a script."""
        # Test the if __name__ == "__main__" path
        with patch("app.main.__name__", "__main__"):
            import importlib

            import app.main

            importlib.reload(app.main)
