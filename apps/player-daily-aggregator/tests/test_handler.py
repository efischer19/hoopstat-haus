"""Test handler module."""

import json
from unittest.mock import Mock, patch

from app.handler import _is_valid_silver_file, lambda_handler


class TestHandler:
    """Test cases for Lambda handler functions."""

    def test_is_valid_silver_file_valid(self):
        """Test valid Silver layer file detection."""
        valid_key = (
            "silver/player_games/season=2023/date=2024-01-15/player_stats.parquet"
        )
        assert _is_valid_silver_file(valid_key) is True

    def test_is_valid_silver_file_invalid_path(self):
        """Test invalid file path detection."""
        invalid_keys = [
            "bronze/player_games/season=2023/date=2024-01-15/player_stats.parquet",
            "silver/team_stats/season=2023/date=2024-01-15/team_stats.parquet",
            "silver/player_games/player_stats.parquet",  # Missing partitions
            "silver/player_games/season=2023/player_stats.csv",  # Wrong format
        ]

        for key in invalid_keys:
            assert _is_valid_silver_file(key) is False

    def test_is_valid_silver_file_missing_partitions(self):
        """Test invalid file without required partitions."""
        invalid_key = "silver/player_games/player_stats.parquet"
        assert _is_valid_silver_file(invalid_key) is False

    def test_is_valid_silver_file_wrong_extension(self):
        """Test invalid file with wrong extension."""
        invalid_key = "silver/player_games/season=2023/date=2024-01-15/player_stats.csv"
        assert _is_valid_silver_file(invalid_key) is False

    @patch("app.handler.LambdaConfig")
    @patch("app.handler.S3Client")
    @patch("app.handler.PlayerStatsAggregator")
    def test_lambda_handler_success(
        self, mock_aggregator_class, mock_s3_class, mock_config_class
    ):
        """Test successful Lambda handler execution."""
        # Mock configuration
        mock_config = Mock()
        mock_config_class.from_environment.return_value = mock_config

        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_class.return_value = mock_s3_client

        # Mock aggregator
        mock_aggregator = Mock()
        mock_aggregator.process_silver_file.return_value = {
            "players_processed": 5,
            "files_written": 10,
            "season": "2023-24",
            "date": "2024-01-15",
        }
        mock_aggregator_class.return_value = mock_aggregator

        # Test event
        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-silver-bucket"},
                        "object": {
                            "key": (
                                "silver/player_games/season=2023/"
                                "date=2024-01-15/player_stats.parquet"
                            )
                        },
                    },
                }
            ]
        }

        # Execute handler
        result = lambda_handler(event, None)

        # Verify result
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "Processed 1 events: 1 successful, 0 failed" in body["message"]
        assert len(body["results"]) == 1
        assert body["results"][0]["status"] == "success"

    @patch("app.handler.LambdaConfig")
    @patch("app.handler.S3Client")
    @patch("app.handler.PlayerStatsAggregator")
    def test_lambda_handler_skip_invalid_file(
        self, mock_aggregator_class, mock_s3_class, mock_config_class
    ):
        """Test Lambda handler skips invalid files."""
        # Mock configuration
        mock_config = Mock()
        mock_config_class.from_environment.return_value = mock_config

        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_class.return_value = mock_s3_client

        # Mock aggregator (should not be called)
        mock_aggregator = Mock()
        mock_aggregator_class.return_value = mock_aggregator

        # Test event with invalid file
        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-silver-bucket"},
                        "object": {
                            "key": (
                                "bronze/player_games/season=2023/"
                                "date=2024-01-15/player_stats.parquet"
                            )
                        },
                    },
                }
            ]
        }

        # Execute handler
        result = lambda_handler(event, None)

        # Verify result
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["results"]) == 1
        assert body["results"][0]["status"] == "skipped"

        # Verify aggregator was not called
        mock_aggregator.process_silver_file.assert_not_called()

    @patch("app.handler.LambdaConfig")
    def test_lambda_handler_config_error(self, mock_config_class):
        """Test Lambda handler handles configuration errors."""
        # Mock configuration to raise error
        mock_config_class.from_environment.side_effect = ValueError(
            "Missing required config"
        )

        # Test event
        event = {"Records": []}

        # Execute handler
        result = lambda_handler(event, None)

        # Verify error result
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Internal server error" in body["message"]

    def test_lambda_handler_empty_event(self):
        """Test Lambda handler with empty event."""
        event = {}

        # This should handle gracefully (no Records key)
        with patch("app.handler.LambdaConfig") as mock_config_class:
            mock_config = Mock()
            mock_config_class.from_environment.return_value = mock_config

            with patch("app.handler.S3Client") as mock_s3_class:
                mock_s3_client = Mock()
                mock_s3_class.return_value = mock_s3_client

                with patch(
                    "app.handler.PlayerStatsAggregator"
                ) as mock_aggregator_class:
                    mock_aggregator = Mock()
                    mock_aggregator_class.return_value = mock_aggregator

                    result = lambda_handler(event, None)

                    assert result["statusCode"] == 200
                    body = json.loads(result["body"])
                    assert "Processed 0 events" in body["message"]
