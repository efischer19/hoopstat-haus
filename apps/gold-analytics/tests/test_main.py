"""Tests for the main CLI module."""

import json

import boto3
import pytest
from click.testing import CliRunner
from moto import mock_aws

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

    def test_status_missing_gold_bucket(self):
        """Test that status command requires gold bucket."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1


class TestGoldStatusCommand:
    """Test cases for the gold layer status command."""

    @pytest.fixture
    def mock_s3(self):
        """Mock S3 for testing."""
        with mock_aws():
            s3_client = boto3.client("s3", region_name="us-east-1")
            s3_client.create_bucket(Bucket="test-gold-bucket")
            yield s3_client

    def _populate_served_artifacts(self, s3_client):
        """Populate S3 with sample served/ artifacts."""
        # Index file
        index_data = {
            "latest_date": "2025-03-20",
            "artifact_types": ["player_daily", "team_daily", "top_lists"],
        }
        s3_client.put_object(
            Bucket="test-gold-bucket",
            Key="served/index/latest.json",
            Body=json.dumps(index_data),
            ContentType="application/json",
        )

        # Player daily artifacts
        s3_client.put_object(
            Bucket="test-gold-bucket",
            Key="served/player_daily/2025-03-20/player_001.json",
            Body=json.dumps({"player_id": "player_001"}),
        )
        s3_client.put_object(
            Bucket="test-gold-bucket",
            Key="served/player_daily/2025-03-20/player_002.json",
            Body=json.dumps({"player_id": "player_002"}),
        )

        # Team daily artifacts
        s3_client.put_object(
            Bucket="test-gold-bucket",
            Key="served/team_daily/2025-03-20/team_001.json",
            Body=json.dumps({"team_id": "team_001"}),
        )

        # Top lists artifacts
        s3_client.put_object(
            Bucket="test-gold-bucket",
            Key="served/top_lists/2025-03-20/points.json",
            Body=json.dumps({"metric": "points"}),
        )

    def test_status_success(self, mock_s3):
        """Test status command succeeds with valid artifacts."""
        self._populate_served_artifacts(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 0

    def test_status_reports_latest_date(self, mock_s3):
        """Test that status reports the latest date from index."""
        self._populate_served_artifacts(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 0
        assert "2025-03-20" in result.output

    def test_status_reports_artifact_counts(self, mock_s3):
        """Test that status reports artifact counts per type."""
        self._populate_served_artifacts(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 0
        assert "player_daily" in result.output
        assert "team_daily" in result.output
        assert "top_lists" in result.output

    def test_status_fails_empty_bucket(self, mock_s3):
        """Test status fails when no artifacts exist under served/."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 1

    def test_status_fails_missing_index(self, mock_s3):
        """Test status fails when index file is missing."""
        # Add an artifact but no index
        mock_s3.put_object(
            Bucket="test-gold-bucket",
            Key="served/player_daily/2025-03-20/player_001.json",
            Body=json.dumps({"player_id": "player_001"}),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 1

    def test_status_fails_invalid_index_json(self, mock_s3):
        """Test status fails when index file is not valid JSON."""
        # Add artifacts with invalid JSON index
        mock_s3.put_object(
            Bucket="test-gold-bucket",
            Key="served/index/latest.json",
            Body="not valid json {{{",
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert result.exit_code == 1

    def test_status_debug_flag(self, mock_s3):
        """Test that debug flag works with status command."""
        self._populate_served_artifacts(mock_s3)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["--debug", "status", "--gold-bucket", "test-gold-bucket"]
        )
        assert result.exit_code == 0

    def test_status_no_warning_messages(self, mock_s3):
        """Test that stub warning messages have been removed."""
        self._populate_served_artifacts(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--gold-bucket", "test-gold-bucket"])
        assert "Health check not yet implemented" not in result.output
        assert "Planned: Check for served/ prefix structure" not in result.output
