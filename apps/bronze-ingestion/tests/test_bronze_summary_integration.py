"""
Integration test for bronze summary generation during ingestion.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.ingestion import DateScopedIngestion


class TestBronzeSummaryIntegration:
    """Test bronze summary integration with ingestion process."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.bronze_bucket = "test-bronze-bucket"
        config.aws_region = "us-east-1"
        return config

    @pytest.fixture
    def ingestion(self, mock_config):
        """Create DateScopedIngestion instance with mocked dependencies."""
        with (
            patch("app.ingestion.NBAClient"),
            patch("app.ingestion.BronzeS3Manager"),
            patch("app.ingestion.DataValidator"),
            patch("app.ingestion.DataQuarantine"),
            patch("app.ingestion.BronzeSummaryManager"),
        ):
            return DateScopedIngestion(mock_config)

    def test_summary_generated_on_successful_ingestion(self, ingestion):
        """Test that bronze summary is generated when ingestion completes."""
        target_date = date(2024, 1, 15)

        # Mock the NBA client to return empty games (no games scenario)
        ingestion.nba_client.get_games_for_date.return_value = []

        # Mock summary manager
        mock_summary_manager = ingestion.summary_manager
        mock_summary_manager.update_bronze_summary.return_value = (
            "_metadata/summary.json"
        )

        # Run ingestion (not dry run)
        result = ingestion.run(target_date, dry_run=False)

        # Verify ingestion was successful
        assert result is True

        # Verify summary was generated
        mock_summary_manager.update_bronze_summary.assert_called_once_with(
            target_date,
            0,
            0,  # 0 games, 0 successful box scores
        )

    def test_summary_not_generated_on_dry_run(self, ingestion):
        """Test that bronze summary is not generated during dry run."""
        target_date = date(2024, 1, 15)

        # Mock the NBA client to return empty games
        ingestion.nba_client.get_games_for_date.return_value = []

        # Mock summary manager
        mock_summary_manager = ingestion.summary_manager

        # Run ingestion as dry run
        result = ingestion.run(target_date, dry_run=True)

        # Verify ingestion was successful
        assert result is True

        # Verify summary was NOT generated
        mock_summary_manager.update_bronze_summary.assert_not_called()

    def test_summary_generated_with_games_and_box_scores(self, ingestion):
        """Test that bronze summary includes correct game and box score counts."""
        target_date = date(2024, 1, 15)

        # Mock games data
        mock_games = [
            {"GAME_ID": "0022400123", "HOME_TEAM_ID": 1, "VISITOR_TEAM_ID": 2},
            {"GAME_ID": "0022400124", "HOME_TEAM_ID": 3, "VISITOR_TEAM_ID": 4},
            {"GAME_ID": "0022400125", "HOME_TEAM_ID": 5, "VISITOR_TEAM_ID": 6},
        ]

        # Mock NBA client responses
        ingestion.nba_client.get_games_for_date.return_value = mock_games
        ingestion.nba_client.get_box_score.return_value = {
            "resultSets": [{"data": "mock_data"}]
        }

        # Mock validation to always pass
        ingestion.validator.validate_api_response.return_value = {
            "valid": True,
            "issues": [],
        }
        ingestion.quarantine.should_quarantine.return_value = False

        # Mock S3 operations
        ingestion.s3_manager.store_parquet.return_value = "test/key"

        # Mock summary manager
        mock_summary_manager = ingestion.summary_manager
        mock_summary_manager.update_bronze_summary.return_value = (
            "_metadata/summary.json"
        )

        # Run ingestion
        result = ingestion.run(target_date, dry_run=False)

        # Verify ingestion was successful
        assert result is True

        # Verify summary was generated with correct counts
        mock_summary_manager.update_bronze_summary.assert_called_once_with(
            target_date,
            3,
            3,  # 3 games, 3 successful box scores
        )

    def test_summary_handles_partial_box_score_failures(self, ingestion):
        """Test that summary correctly tracks partial box score failures."""
        target_date = date(2024, 1, 15)

        # Mock games data
        mock_games = [
            {"GAME_ID": "0022400123", "HOME_TEAM_ID": 1, "VISITOR_TEAM_ID": 2},
            {"GAME_ID": "0022400124", "HOME_TEAM_ID": 3, "VISITOR_TEAM_ID": 4},
            {"GAME_ID": "0022400125", "HOME_TEAM_ID": 5, "VISITOR_TEAM_ID": 6},
        ]

        # Mock NBA client - schedule works, but some box scores fail
        ingestion.nba_client.get_games_for_date.return_value = mock_games

        # Mock box score responses - first succeeds, second fails, third succeeds
        box_score_responses = [
            {"resultSets": [{"data": "mock_data_1"}]},
            None,  # This will be treated as a failure
            {"resultSets": [{"data": "mock_data_3"}]},
        ]
        ingestion.nba_client.get_box_score.side_effect = box_score_responses

        # Mock validation
        ingestion.validator.validate_api_response.return_value = {
            "valid": True,
            "issues": [],
        }
        ingestion.quarantine.should_quarantine.return_value = False

        # Mock S3 operations
        ingestion.s3_manager.store_parquet.return_value = "test/key"

        # Mock summary manager
        mock_summary_manager = ingestion.summary_manager
        mock_summary_manager.update_bronze_summary.return_value = (
            "_metadata/summary.json"
        )

        # Run ingestion
        result = ingestion.run(target_date, dry_run=False)

        # Verify ingestion was successful
        assert result is True

        # Verify summary shows partial success: 3 games found, only 2 box scores
        # succeeded
        mock_summary_manager.update_bronze_summary.assert_called_once_with(
            target_date,
            3,
            2,  # 3 games, 2 successful box scores
        )
