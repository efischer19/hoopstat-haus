"""Tests for the ingestion module."""

from datetime import date
from unittest.mock import Mock, patch

from app.config import BronzeIngestionConfig
from app.ingestion import DateScopedIngestion


class TestDateScopedIngestion:
    """Test the date-scoped ingestion functionality."""

    @patch("app.ingestion.DataValidator")
    @patch("app.ingestion.DataQuarantine")
    @patch("app.ingestion.NBAClient")
    @patch("app.ingestion.BronzeS3Manager")
    def test_run_no_games(
        self, mock_s3_manager, mock_nba_client, mock_quarantine, mock_validator
    ):
        """Test ingestion when no games are found for the date."""
        # Mock configuration
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        # Mock NBA client to return no games
        mock_client_instance = Mock()
        mock_client_instance.get_games_for_date.return_value = []
        mock_nba_client.return_value = mock_client_instance

        # Mock S3 manager
        mock_s3_instance = Mock()
        mock_s3_manager.return_value = mock_s3_instance

        # Mock validator and quarantine
        mock_validator_instance = Mock()
        mock_validator_instance.validate_api_response.return_value = {
            "valid": True,
            "issues": [],
            "metrics": {"schema_valid": True},
        }
        mock_validator.return_value = mock_validator_instance

        mock_quarantine_instance = Mock()
        mock_quarantine_instance.should_quarantine.return_value = False
        mock_quarantine.return_value = mock_quarantine_instance

        # Create ingestion instance
        ingestion = DateScopedIngestion(config)

        # Run ingestion
        target_date = date(2023, 8, 15)  # Off-season date
        result = ingestion.run(target_date, dry_run=False)

        # Assert success with early exit
        assert result is True
        mock_client_instance.get_games_for_date.assert_called_once_with(target_date)
        mock_s3_instance.store_parquet.assert_not_called()

    @patch("app.ingestion.DataValidator")
    @patch("app.ingestion.DataQuarantine")
    @patch("app.ingestion.NBAClient")
    @patch("app.ingestion.BronzeS3Manager")
    def test_run_with_games_dry_run(
        self, mock_s3_manager, mock_nba_client, mock_quarantine, mock_validator
    ):
        """Test ingestion with games in dry run mode."""
        # Mock configuration
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        # Mock NBA client to return games with valid schema-compliant data
        mock_games = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612747,  # Required field
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "PTS": 110,
            },
            {
                "GAME_ID": "1234567891",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612738,  # Required field
                "TEAM_ABBREVIATION": "BOS",
                "TEAM_NAME": "Boston Celtics",
                "PTS": 105,
            },
        ]
        mock_box_score = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [["123", "LeBron James", 25]],
                }
            ],
            "parameters": {"GameID": "1234567890"},
        }

        mock_client_instance = Mock()
        mock_client_instance.get_games_for_date.return_value = mock_games
        mock_client_instance.get_box_score.return_value = mock_box_score
        mock_nba_client.return_value = mock_client_instance

        # Mock S3 manager
        mock_s3_instance = Mock()
        mock_s3_manager.return_value = mock_s3_instance

        # Mock validator to return valid results
        mock_validator_instance = Mock()
        mock_validator_instance.validate_api_response.return_value = {
            "valid": True,
            "issues": [],
            "metrics": {"schema_valid": True},
        }
        mock_validator_instance.validate_completeness.return_value = {
            "complete": True,
            "actual_count": 2,
            "expected_count": None,
            "issues": [],
        }
        mock_validator.return_value = mock_validator_instance

        # Mock quarantine
        mock_quarantine_instance = Mock()
        mock_quarantine_instance.should_quarantine.return_value = False
        mock_quarantine.return_value = mock_quarantine_instance

        # Create ingestion instance
        ingestion = DateScopedIngestion(config)

        # Run ingestion in dry run mode
        target_date = date(2023, 12, 25)
        result = ingestion.run(target_date, dry_run=True)

        # Assert success but no S3 writes
        assert result is True
        mock_client_instance.get_games_for_date.assert_called_once_with(target_date)
        mock_s3_instance.store_parquet.assert_not_called()

    @patch("app.ingestion.DataValidator")
    @patch("app.ingestion.DataQuarantine")
    @patch("app.ingestion.NBAClient")
    @patch("app.ingestion.BronzeS3Manager")
    def test_run_with_games_actual_ingestion(
        self, mock_s3_manager, mock_nba_client, mock_quarantine, mock_validator
    ):
        """Test actual ingestion with games."""
        # Mock configuration
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        # Mock NBA client to return games with valid schema-compliant data
        mock_games = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612747,  # Required field
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "PTS": 110,
            }
        ]
        mock_box_score = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [["123", "LeBron James", 25]],
                }
            ],
            "parameters": {"GameID": "1234567890"},
        }

        mock_client_instance = Mock()
        mock_client_instance.get_games_for_date.return_value = mock_games
        mock_client_instance.get_box_score.return_value = mock_box_score
        mock_nba_client.return_value = mock_client_instance

        # Mock S3 manager
        mock_s3_instance = Mock()
        mock_s3_manager.return_value = mock_s3_instance

        # Mock validator to return valid results
        mock_validator_instance = Mock()
        mock_validator_instance.validate_api_response.return_value = {
            "valid": True,
            "issues": [],
            "metrics": {"schema_valid": True},
        }
        mock_validator_instance.validate_completeness.return_value = {
            "complete": True,
            "actual_count": 1,
            "expected_count": None,
            "issues": [],
        }
        mock_validator.return_value = mock_validator_instance

        # Mock quarantine
        mock_quarantine_instance = Mock()
        mock_quarantine_instance.should_quarantine.return_value = False
        mock_quarantine.return_value = mock_quarantine_instance

        # Create ingestion instance
        ingestion = DateScopedIngestion(config)

        # Run ingestion
        target_date = date(2023, 12, 25)
        result = ingestion.run(target_date, dry_run=False)

        # Assert success with S3 writes
        assert result is True
        mock_client_instance.get_games_for_date.assert_called_once_with(target_date)

        # Should store schedule and box score
        assert mock_s3_instance.store_parquet.call_count == 2

        # Verify schedule storage call
        schedule_call = mock_s3_instance.store_parquet.call_args_list[0]
        assert schedule_call[1]["entity"] == "schedule"
        assert schedule_call[1]["target_date"] == target_date

        # Verify box score storage call
        box_score_call = mock_s3_instance.store_parquet.call_args_list[1]
        assert box_score_call[1]["entity"] == "box_scores"
        assert box_score_call[1]["target_date"] == target_date
        assert box_score_call[1]["partition_suffix"] == "/1234567890"

    def test_flatten_box_score(self):
        """Test box score flattening logic."""
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        with (
            patch("app.ingestion.DataValidator"),
            patch("app.ingestion.DataQuarantine"),
            patch("app.ingestion.NBAClient"),
            patch("app.ingestion.BronzeS3Manager"),
        ):
            ingestion = DateScopedIngestion(config)

            # Test with complete box score data
            box_score = {
                "game_id": "12345",
                "fetch_date": "2023-12-25T10:00:00",
                "resultSets": [
                    {
                        "name": "TeamStats",
                        "rowSet": [["LAL", 100, 45, 20], ["GSW", 95, 40, 18]],
                    }
                ],
            }

            flattened = ingestion._flatten_box_score(box_score)

            assert flattened["game_id"] == "12345"
            assert flattened["fetch_date"] == "2023-12-25T10:00:00"
            assert flattened["result_set_name"] == "TeamStats"
            assert flattened["row_count"] == 2

    def test_flatten_box_score_empty(self):
        """Test box score flattening with minimal data."""
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        with (
            patch("app.ingestion.DataValidator"),
            patch("app.ingestion.DataQuarantine"),
            patch("app.ingestion.NBAClient"),
            patch("app.ingestion.BronzeS3Manager"),
        ):
            ingestion = DateScopedIngestion(config)

            # Test with minimal box score data
            box_score = {"game_id": "12345", "fetch_date": "2023-12-25T10:00:00"}

            flattened = ingestion._flatten_box_score(box_score)

            assert flattened["game_id"] == "12345"
            assert flattened["fetch_date"] == "2023-12-25T10:00:00"
            assert "result_set_name" not in flattened
            assert "row_count" not in flattened

    @patch("app.ingestion.DataValidator")
    @patch("app.ingestion.DataQuarantine")
    @patch("app.ingestion.NBAClient")
    @patch("app.ingestion.BronzeS3Manager")
    def test_api_failure_handling(
        self, mock_s3_manager, mock_nba_client, mock_quarantine, mock_validator
    ):
        """Test handling of API failures."""
        # Mock configuration
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        # Mock NBA client to raise exception
        mock_client_instance = Mock()
        mock_client_instance.get_games_for_date.side_effect = Exception("API Error")
        mock_nba_client.return_value = mock_client_instance

        # Mock S3 manager
        mock_s3_instance = Mock()
        mock_s3_manager.return_value = mock_s3_instance

        # Mock validator and quarantine (though they won't be called due to API failure)
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance

        mock_quarantine_instance = Mock()
        mock_quarantine.return_value = mock_quarantine_instance

        # Create ingestion instance
        ingestion = DateScopedIngestion(config)

        # Run ingestion - should handle exception gracefully
        target_date = date(2023, 12, 25)
        result = ingestion.run(target_date, dry_run=False)

        # Assert failure
        assert result is False
        mock_s3_instance.store_parquet.assert_not_called()
