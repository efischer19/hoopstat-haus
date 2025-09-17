"""Tests for the handlers module."""

import os
from unittest.mock import MagicMock, patch

from app.handlers import lambda_handler


class TestLambdaHandler:
    """Test cases for the Lambda handler."""

    @patch.dict(os.environ, {"SILVER_BUCKET": "test-silver", "GOLD_BUCKET": "test-gold"})
    @patch("app.handlers.GoldProcessor")
    def test_lambda_handler_basic(self, mock_processor_class):
        """Test basic lambda handler invocation."""
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        event = {"Records": []}
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert "message" in response["body"]
        assert response["body"]["records_processed"] == 0

    @patch.dict(os.environ, {"SILVER_BUCKET": "test-silver", "GOLD_BUCKET": "test-gold"})
    @patch("app.handlers.GoldProcessor")
    @patch("app.handlers.parse_s3_event_key")
    def test_lambda_handler_with_records(self, mock_parse_key, mock_processor_class):
        """Test lambda handler with S3 event records."""
        from datetime import date

        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor.process_date.return_value = True
        mock_processor_class.return_value = mock_processor

        # Setup mock S3 key parser
        mock_parse_key.return_value = {
            "file_type": "player_stats",
            "season": "2023-24",
            "date": date(2024, 1, 15),
            "original_key": "silver/player_stats/season=2023-24/date=2024-01-15/file.parquet",
        }

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "silver/player_stats/season=2023-24/date=2024-01-15/file.parquet"},
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "silver/player_stats/season=2023-24/date=2024-01-15/file2.parquet"},
                    }
                },
            ]
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"]["records_processed"] == 1  # One unique date processed
        # Verify processor was called
        mock_processor.process_date.assert_called_once_with(date(2024, 1, 15), dry_run=False)

    @patch.dict(os.environ, {"SILVER_BUCKET": "test-silver", "GOLD_BUCKET": "test-gold"})
    @patch("app.handlers.GoldProcessor")
    def test_lambda_handler_no_records(self, mock_processor_class):
        """Test lambda handler with event that has no Records."""
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        event = {"test": "data"}
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"]["records_processed"] == 0

    @patch.dict(os.environ, {"SILVER_BUCKET": "test-silver", "GOLD_BUCKET": "test-gold"})
    @patch("app.handlers.GoldProcessor")
    @patch("app.handlers.parse_s3_event_key")
    def test_lambda_handler_invalid_s3_key(self, mock_parse_key, mock_processor_class):
        """Test lambda handler with invalid S3 key that can't be parsed."""
        # Setup mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        # Setup mock S3 key parser to return None (unparseable key)
        mock_parse_key.return_value = None

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "invalid/key/structure"},
                    }
                },
            ]
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"]["records_processed"] == 0
        # Verify processor was not called since key couldn't be parsed
        mock_processor.process_date.assert_not_called()

    def test_lambda_handler_missing_environment_variables(self):
        """Test lambda handler with missing environment variables."""
        event = {"Records": []}
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response["statusCode"] == 500
        assert "error" in response["body"]
        assert "SILVER_BUCKET" in response["body"]["error"]
