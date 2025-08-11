"""Tests for the bronze layer ingestion main module."""

from datetime import UTC, timezone
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

    @patch("app.main.BronzeIngester")
    @patch("app.main.BronzeIngestionConfig")
    def test_ingest_command_with_date(self, mock_config, mock_ingester):
        """Test the ingest command with explicit date."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config.load.return_value = mock_config_instance

        # Mock ingester
        mock_ingester_instance = Mock()
        mock_ingester.return_value = mock_ingester_instance
        mock_ingester_instance.ingest_for_date.return_value = {
            "schedule": 10,
            "box_score": 100,
            "play_by_play": 500,
        }

        result = self.runner.invoke(
            cli, ["ingest", "--date", "2024-01-15", "--dry-run"]
        )
        assert result.exit_code == 0

        # Verify ingester was called with correct parameters
        mock_ingester.assert_called_once_with(mock_config_instance)
        mock_ingester_instance.ingest_for_date.assert_called_once_with(
            "2024-01-15", dry_run=True
        )

    @patch("app.main.BronzeIngester")
    @patch("app.main.BronzeIngestionConfig")
    @patch("app.main.datetime")
    def test_ingest_command_default_date_utc(
        self, mock_datetime, mock_config, mock_ingester
    ):
        """Test the ingest command uses today UTC when no date provided."""
        # Mock current time
        mock_now = Mock()
        mock_now.strftime.return_value = "2024-01-15"
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone = timezone

        # Mock configuration
        mock_config_instance = Mock()
        mock_config.load.return_value = mock_config_instance

        # Mock ingester
        mock_ingester_instance = Mock()
        mock_ingester.return_value = mock_ingester_instance
        mock_ingester_instance.ingest_for_date.return_value = {
            "schedule": 5,
            "box_score": 50,
            "play_by_play": 250,
        }

        result = self.runner.invoke(cli, ["ingest", "--dry-run"])
        assert result.exit_code == 0

        # Verify today UTC was requested
        mock_datetime.now.assert_called_once_with(UTC)
        mock_ingester_instance.ingest_for_date.assert_called_once_with(
            "2024-01-15", dry_run=True
        )

    def test_ingest_command_invalid_date_format(self):
        """Test the ingest command handles invalid date format."""
        result = self.runner.invoke(cli, ["ingest", "--date", "invalid-date"])
        assert result.exit_code == 1
        # The error is logged to stderr, but click runner doesn't capture logs

    @patch("app.main.BronzeIngester")
    @patch("app.main.BronzeIngestionConfig")
    def test_ingest_command_handles_errors(self, mock_config, mock_ingester):
        """Test the ingest command handles ingestion errors."""
        # Mock configuration
        mock_config.load.side_effect = Exception("Config error")

        result = self.runner.invoke(cli, ["ingest", "--date", "2024-01-15"])
        assert result.exit_code == 1

    @patch("app.s3_client.S3ParquetClient")
    @patch("app.main.BronzeIngestionConfig")
    def test_status_command(self, mock_config, mock_s3_client):
        """Test the status command runs successfully."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config_instance.bronze_bucket_name = "test-bucket"
        mock_config.load.return_value = mock_config_instance

        # Mock S3 client
        mock_s3_client_instance = Mock()
        mock_s3_client.return_value = mock_s3_client_instance

        result = self.runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    @patch("app.main.BronzeIngestionConfig")
    def test_status_command_handles_errors(self, mock_config):
        """Test the status command handles configuration errors."""
        mock_config.load.side_effect = Exception("Config error")

        result = self.runner.invoke(cli, ["status"])
        assert result.exit_code == 1


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
