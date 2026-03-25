"""Tests for the main CLI module."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from click.testing import CliRunner

from app.main import cli


class TestCLI:
    """Test cases for the CLI interface."""

    def test_cli_help(self):
        """Test that CLI shows help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Gold layer analytics processing pipeline" in result.output

    def test_process_help(self):
        """Test that process command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process Silver layer data" in result.output

    def test_status_help(self):
        """Test that status command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Check the status" in result.output

    def test_debug_flag(self):
        """Test that debug flag is accepted."""
        runner = CliRunner()
        with patch("app.main.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.list_objects_v2.return_value = {"KeyCount": 0}
            mock_s3.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
            )
            result = runner.invoke(
                cli, ["--debug", "status", "--gold-bucket", "test-bucket"]
            )
        assert result.exit_code == 0

    def test_dry_run_flag(self):
        """Test that dry-run flag works."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "process",
                "--dry-run",
                "--silver-bucket",
                "test-silver-bucket",
                "--gold-bucket",
                "test-gold-bucket",
            ],
        )
        # Should succeed in dry-run mode with mock data
        assert result.exit_code == 0

    def test_missing_silver_bucket(self):
        """Test that missing silver bucket causes error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process"])
        assert result.exit_code == 1

    def test_missing_gold_bucket(self):
        """Test that missing gold bucket causes error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process", "--silver-bucket", "test-bucket"])
        assert result.exit_code == 1

    def test_status_checks_artifact_prefixes(self):
        """Test that status command checks served/ artifact prefixes in S3."""
        runner = CliRunner()
        with patch("app.main.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.list_objects_v2.return_value = {"KeyCount": 1}
            mock_s3.head_object.return_value = {}
            result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 0
        # Verify all 5 artifact prefixes were checked
        assert mock_s3.list_objects_v2.call_count == 5
        mock_s3.head_object.assert_called_once()

    def test_status_missing_gold_bucket(self):
        """Test that status command requires gold bucket."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1
