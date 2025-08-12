"""Tests for the bronze layer ingestion main module."""

from datetime import datetime
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

    @patch("app.main.DateScopedIngestion")
    @patch("app.main.get_logger")
    def test_ingest_command(self, mock_logger, mock_ingestion_class):
        """Test the ingest command runs successfully."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # Mock the ingestion
        mock_ingestion = Mock()
        mock_ingestion.run.return_value = True
        mock_ingestion_class.return_value = mock_ingestion

        result = self.runner.invoke(cli, ["ingest", "--dry-run"])
        assert result.exit_code == 0

        # Verify ingestion was called with correct parameters
        mock_ingestion.run.assert_called_once()
        call_args = mock_ingestion.run.call_args
        assert call_args[1]["dry_run"] is True
        # Should default to today's date
        assert isinstance(call_args[1]["target_date"], type(datetime.utcnow().date()))

    @patch("app.main.DateScopedIngestion")
    @patch("app.main.get_logger")
    def test_ingest_command_with_date(self, mock_logger, mock_ingestion_class):
        """Test the ingest command with custom date."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # Mock the ingestion
        mock_ingestion = Mock()
        mock_ingestion.run.return_value = True
        mock_ingestion_class.return_value = mock_ingestion

        result = self.runner.invoke(
            cli, ["ingest", "--date", "2023-12-25", "--dry-run"]
        )
        assert result.exit_code == 0

        # Verify ingestion was called with the specified date
        mock_ingestion.run.assert_called_once()
        call_args = mock_ingestion.run.call_args
        assert call_args[1]["dry_run"] is True
        assert str(call_args[1]["target_date"]) == "2023-12-25"

    @patch("app.main.DateScopedIngestion")
    @patch("app.main.get_logger")
    def test_ingest_command_failure(self, mock_logger, mock_ingestion_class):
        """Test the ingest command handles failures."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # Mock the ingestion to fail
        mock_ingestion = Mock()
        mock_ingestion.run.return_value = False
        mock_ingestion_class.return_value = mock_ingestion

        result = self.runner.invoke(cli, ["ingest", "--dry-run"])
        assert result.exit_code == 1

    @patch("app.main.DateScopedIngestion")
    @patch("app.main.get_logger")
    def test_status_command(self, mock_logger, mock_ingestion_class):
        """Test the status command runs successfully."""
        # Mock the logger
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance

        # Mock the ingestion initialization
        mock_ingestion = Mock()
        mock_ingestion_class.return_value = mock_ingestion

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
