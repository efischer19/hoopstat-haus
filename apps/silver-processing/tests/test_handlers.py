"""Tests for the Lambda handlers module."""

from datetime import date
from unittest.mock import MagicMock, patch

from app.handlers import lambda_handler


class TestLambdaHandler:
    """Test cases for Lambda event handlers."""

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_non_summary_event(self, mock_s3_manager):
        """Test Lambda handler with non-summary event."""
        mock_manager = MagicMock()
        mock_s3_manager.return_value = mock_manager

        # Event for a regular file, not summary.json
        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "raw/box/2024-01-15/data.json"},
                    },
                }
            ]
        }
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 200
        assert "Event ignored" in result["message"]

    @patch.dict("os.environ", {}, clear=True)
    def test_lambda_handler_no_bucket_configured(self):
        """Test Lambda handler with no bucket configured."""
        event = {}
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 400
        assert "bronze bucket configured" in result["message"]

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_with_summary_update(self, mock_s3_manager):
        """Test Lambda handler with summary.json update event."""
        # Mock S3 manager to return summary data
        mock_manager = MagicMock()
        mock_manager.read_summary_json.return_value = {
            "summary_version": "1.0",
            "bronze_layer_stats": {"last_ingestion_date": "2024-01-15"},
        }
        mock_s3_manager.return_value = mock_manager

        # Mock the processor to succeed
        with patch("app.handlers.SilverProcessor") as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_date.return_value = True
            mock_processor_class.return_value = mock_processor

            event = {
                "Records": [
                    {
                        "eventSource": "aws:s3",
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "_metadata/summary.json"},
                        },
                    }
                ]
            }
            context = {}
            result = lambda_handler(event, context)

            assert result["statusCode"] == 200
            assert "Successfully processed" in result["message"]
            assert "2024-01-15" in result["message"]

            # Verify the processor was called with the correct date
            mock_processor.process_date.assert_called_once_with(
                date(2024, 1, 15), dry_run=False
            )

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_summary_not_found(self, mock_s3_manager):
        """Test Lambda handler when summary.json doesn't exist."""
        mock_manager = MagicMock()
        mock_manager.read_summary_json.return_value = None
        mock_s3_manager.return_value = mock_manager

        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "_metadata/summary.json"},
                    },
                }
            ]
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 404
        assert "Summary file not found" in result["message"]

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_no_date_in_summary(self, mock_s3_manager):
        """Test Lambda handler when summary has no last_ingestion_date."""
        mock_manager = MagicMock()
        mock_manager.read_summary_json.return_value = {
            "summary_version": "1.0",
            "bronze_layer_stats": {},  # Missing last_ingestion_date
        }
        mock_s3_manager.return_value = mock_manager

        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "_metadata/summary.json"},
                    },
                }
            ]
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 200
        assert "No date found in summary" in result["message"]

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_processing_failure(self, mock_s3_manager):
        """Test Lambda handler when processing fails."""
        mock_manager = MagicMock()
        mock_manager.read_summary_json.return_value = {
            "summary_version": "1.0",
            "bronze_layer_stats": {"last_ingestion_date": "2024-01-15"},
        }
        mock_s3_manager.return_value = mock_manager

        # Mock the processor to fail
        with patch("app.handlers.SilverProcessor") as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_date.return_value = False
            mock_processor_class.return_value = mock_processor

            event = {
                "Records": [
                    {
                        "eventSource": "aws:s3",
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "_metadata/summary.json"},
                        },
                    }
                ]
            }
            context = {}
            result = lambda_handler(event, context)

            assert result["statusCode"] == 500
            assert "Processing failed" in result["message"]

    @patch("app.handlers.SilverS3Manager")
    @patch.dict("os.environ", {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"})
    def test_lambda_handler_exception_during_processing(self, mock_s3_manager):
        """Test Lambda handler when an exception occurs during processing."""
        mock_manager = MagicMock()
        mock_manager.read_summary_json.side_effect = Exception("S3 read error")
        mock_s3_manager.return_value = mock_manager

        event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "_metadata/summary.json"},
                    },
                }
            ]
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 500
        assert "Failed to process summary update" in result["message"]
