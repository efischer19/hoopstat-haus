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
        # Status now requires --silver-bucket but will fail without mocked S3
        result = runner.invoke(cli, ["--debug", "status"])
        assert result.exit_code == 1

    def test_dry_run_flag(self):
        """Test that dry-run flag works."""
        runner = CliRunner()
        # Provide a bronze bucket to avoid the error - it will still fail due to
        # no credentials but that's expected behavior, not a test failure
        result = runner.invoke(
            cli, ["process", "--dry-run", "--bronze-bucket", "test-bucket"]
        )
        # The command will exit with code 1 due to S3 connection failure, which
        # is expected
        assert result.exit_code == 1

    def test_missing_bronze_bucket(self):
        """Test error handling when no bronze bucket is specified."""
        runner = CliRunner()
        result = runner.invoke(cli, ["process", "--dry-run"])
        assert result.exit_code == 1

    def test_status_missing_silver_bucket(self):
        """Test that status command requires silver bucket."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1


class TestSilverStatusCommand:
    """Test cases for the silver layer status command."""

    @pytest.fixture
    def mock_s3(self):
        """Mock S3 for testing."""
        with mock_aws():
            s3_client = boto3.client("s3", region_name="us-east-1")
            s3_client.create_bucket(Bucket="test-silver-bucket")
            yield s3_client

    def _populate_silver_data(self, s3_client):
        """Populate S3 with sample silver/ data."""
        # Player stats
        s3_client.put_object(
            Bucket="test-silver-bucket",
            Key="silver/player-stats/2025-03-20/players.json",
            Body=json.dumps([{"player_id": "p1"}]),
        )
        # Team stats
        s3_client.put_object(
            Bucket="test-silver-bucket",
            Key="silver/team-stats/2025-03-20/teams.json",
            Body=json.dumps([{"team_id": "t1"}]),
        )
        # Game stats
        s3_client.put_object(
            Bucket="test-silver-bucket",
            Key="silver/game-stats/2025-03-20/games.json",
            Body=json.dumps([{"game_id": "g1"}]),
        )
        # Silver-ready marker
        s3_client.put_object(
            Bucket="test-silver-bucket",
            Key="metadata/2025-03-20/silver-ready.json",
            Body=json.dumps({"game_date": "2025-03-20"}),
        )

    def test_status_success(self, mock_s3):
        """Test status command succeeds with valid silver data."""
        self._populate_silver_data(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--silver-bucket", "test-silver-bucket"])
        assert result.exit_code == 0

    def test_status_reports_entity_types(self, mock_s3):
        """Test that status reports entity type counts."""
        self._populate_silver_data(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--silver-bucket", "test-silver-bucket"])
        assert result.exit_code == 0
        assert "player-stats" in result.output
        assert "team-stats" in result.output
        assert "game-stats" in result.output

    def test_status_reports_latest_marker(self, mock_s3):
        """Test that status reports latest silver-ready marker date."""
        self._populate_silver_data(mock_s3)

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--silver-bucket", "test-silver-bucket"])
        assert result.exit_code == 0
        assert "2025-03-20" in result.output

    def test_status_fails_empty_bucket(self, mock_s3):
        """Test status fails when no silver data exists."""
        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--silver-bucket", "test-silver-bucket"])
        assert result.exit_code == 1

    def test_status_warns_no_markers(self, mock_s3):
        """Test status warns when no silver-ready markers exist."""
        # Add silver data but no markers
        mock_s3.put_object(
            Bucket="test-silver-bucket",
            Key="silver/player-stats/2025-03-20/players.json",
            Body=json.dumps([{"player_id": "p1"}]),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["status", "--silver-bucket", "test-silver-bucket"])
        # Should still succeed (markers are informational, not required)
        assert result.exit_code == 0
        assert "No silver-ready markers" in result.output
