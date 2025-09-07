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
        mock_s3_instance.store_json.assert_not_called()

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
        mock_s3_instance.store_json.assert_not_called()

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

        # Should store both schedule and box score as JSON
        assert mock_s3_instance.store_json.call_count == 2

        # Verify schedule storage call (JSON)
        schedule_call = mock_s3_instance.store_json.call_args_list[0]
        assert schedule_call[1]["entity"] == "schedule"
        assert schedule_call[1]["target_date"] == target_date

        # Verify box score storage call (JSON)
        box_score_call = mock_s3_instance.store_json.call_args_list[1]
        assert box_score_call[1]["entity"] == "box_scores"
        assert box_score_call[1]["target_date"] == target_date

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

    @patch("app.ingestion.DataValidator")
    @patch("app.ingestion.DataQuarantine")
    @patch("app.ingestion.NBAClient")
    @patch("app.ingestion.BronzeS3Manager")
    def test_schedule_json_storage_integration(
        self, mock_s3_manager, mock_nba_client, mock_quarantine, mock_validator
    ):
        """Test that schedule data is stored as valid JSON and is readable."""
        import json

        # Mock configuration
        config = BronzeIngestionConfig(
            bronze_bucket="test-bucket", aws_region="us-east-1"
        )

        # Mock games data in NBA API format
        mock_games = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612747,
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "PTS": 110,
            },
            {
                "GAME_ID": "1234567891",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 1610612744,
                "TEAM_ABBREVIATION": "GSW",
                "TEAM_NAME": "Golden State Warriors",
                "PTS": 105,
            },
        ]

        # Mock box score data
        mock_box_score = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [["123", "Player 1", 25]],
                }
            ],
            "parameters": {"GameID": "1234567890"},
        }

        # Mock NBA client
        mock_client_instance = Mock()
        mock_client_instance.get_games_for_date.return_value = mock_games
        mock_client_instance.get_box_score.return_value = mock_box_score
        mock_nba_client.return_value = mock_client_instance

        # Mock S3 manager to capture stored JSON data
        mock_s3_instance = Mock()
        stored_schedule_data = None

        def capture_json_storage(data, entity, target_date):
            nonlocal stored_schedule_data
            if entity == "schedule":
                stored_schedule_data = data
            return f"raw/{entity}/date={target_date.strftime('%Y-%m-%d')}/data.json"

        mock_s3_instance.store_json.side_effect = capture_json_storage
        mock_s3_manager.return_value = mock_s3_instance

        # Mock validator
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

        # Run ingestion
        target_date = date(2023, 12, 25)
        result = ingestion.run(target_date, dry_run=False)

        # Assert success
        assert result is True

        # Verify JSON storage was called 3 times (1 schedule + 2 box scores)
        assert mock_s3_instance.store_json.call_count == 3

        # Verify the stored data is the original games list (no DataFrame conversion)
        assert stored_schedule_data == mock_games

        # Verify the stored data can be serialized to JSON and parsed back
        json_str = json.dumps(stored_schedule_data)
        parsed_data = json.loads(json_str)

        # Verify the JSON structure is correct
        assert isinstance(parsed_data, list)
        assert len(parsed_data) == 2
        assert parsed_data[0]["GAME_ID"] == "1234567890"
        assert parsed_data[0]["TEAM_ABBREVIATION"] == "LAL"
        assert parsed_data[1]["GAME_ID"] == "1234567891"
        assert parsed_data[1]["TEAM_ABBREVIATION"] == "GSW"
