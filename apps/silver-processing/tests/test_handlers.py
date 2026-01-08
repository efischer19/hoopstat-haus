"""Tests for the Lambda handlers module."""

from datetime import date
from unittest.mock import MagicMock, patch

from app.handlers import lambda_handler


class TestLambdaHandler:
    """Test cases for Lambda event handlers."""

    @patch("app.handlers.SilverS3Manager")
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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
    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
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

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_single_date(self):
        """Test Lambda handler with manual single date invocation."""
        with patch("app.handlers.SilverProcessor") as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_date.return_value = True
            mock_processor_class.return_value = mock_processor

            event = {
                "source": "github-actions-manual",
                "trigger_type": "workflow_dispatch",
                "parameters": {"date": "2024-01-15", "dry_run": True},
            }
            context = {}
            result = lambda_handler(event, context)

            assert result["statusCode"] == 200
            mock_processor.process_date.assert_called_once_with(
                date(2024, 1, 15), dry_run=True
            )

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_date_range(self):
        """Test Lambda handler with manual date range invocation."""
        with patch("app.handlers.SilverProcessor") as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_date.return_value = True
            mock_processor_class.return_value = mock_processor

            event = {
                "source": "github-actions-manual",
                "trigger_type": "workflow_dispatch",
                "parameters": {
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-17",
                    "dry_run": False,
                },
            }
            context = {}
            result = lambda_handler(event, context)

            assert result["statusCode"] == 200
            assert result["start_date"] == "2024-01-15"
            assert result["end_date"] == "2024-01-17"
            assert mock_processor.process_date.call_count == 3
            mock_processor.process_date.assert_any_call(
                date(2024, 1, 15), dry_run=False
            )
            mock_processor.process_date.assert_any_call(
                date(2024, 1, 16), dry_run=False
            )
            mock_processor.process_date.assert_any_call(
                date(2024, 1, 17), dry_run=False
            )

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_invalid_date_format(self):
        """Test Lambda handler with invalid date format in manual invocation."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {"date": "2024-13-45"},  # Invalid date
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid date format" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_invalid_date_string(self):
        """Test Lambda handler with non-date string in manual invocation."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {"date": "not-a-date"},
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid date format" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_invalid_range_format(self):
        """Test Lambda handler with invalid date range format."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {
                "start_date": "2024-01-15",
                "end_date": "invalid-date",
            },
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid date format or range" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_start_after_end(self):
        """Test Lambda handler when start_date is after end_date."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {
                "start_date": "2024-01-20",
                "end_date": "2024-01-15",
            },
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid date format or range" in result["message"]
        assert "start_date must be <= end_date" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_empty_date_strings(self):
        """Test Lambda handler with empty date strings in range."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {
                "start_date": "",
                "end_date": "",
            },
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid manual parameters" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_missing_parameters(self):
        """Test Lambda handler with empty parameters dict."""
        event = {
            "source": "github-actions-manual",
            "trigger_type": "workflow_dispatch",
            "parameters": {},
        }
        context = {}
        result = lambda_handler(event, context)

        assert result["statusCode"] == 400
        assert "Invalid manual parameters" in result["message"]

    @patch.dict(
        "os.environ",
        {"BRONZE_BUCKET": "test-bucket", "SILVER_BUCKET": "test-silver-bucket"},
    )
    def test_lambda_handler_manual_date_range_partial_failures(self):
        """Test Lambda handler with date range where some dates fail."""
        with patch("app.handlers.SilverProcessor") as mock_processor_class:
            mock_processor = MagicMock()
            # Simulate failure for the second date
            mock_processor.process_date.side_effect = [True, False, True]
            mock_processor_class.return_value = mock_processor

            event = {
                "source": "github-actions-manual",
                "trigger_type": "workflow_dispatch",
                "parameters": {
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-17",
                    "dry_run": False,
                },
            }
            context = {}
            result = lambda_handler(event, context)

            assert result["statusCode"] == 500
            assert "Processing failed for some dates" in result["message"]
            assert "failures" in result
            assert "2024-01-16" in result["failures"]


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_parse_yyyy_mm_dd_valid_date(self):
        """Test parsing a valid date string."""
        from app.handlers import _parse_yyyy_mm_dd

        result = _parse_yyyy_mm_dd("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_yyyy_mm_dd_invalid_format(self):
        """Test parsing an invalid date format raises ValueError."""
        import pytest

        from app.handlers import _parse_yyyy_mm_dd

        with pytest.raises(ValueError):
            _parse_yyyy_mm_dd("01-15-2024")  # Wrong format

    def test_parse_yyyy_mm_dd_invalid_date(self):
        """Test parsing an invalid date raises ValueError."""
        import pytest

        from app.handlers import _parse_yyyy_mm_dd

        with pytest.raises(ValueError):
            _parse_yyyy_mm_dd("2024-13-45")  # Invalid month and day

    def test_parse_yyyy_mm_dd_non_date_string(self):
        """Test parsing a non-date string raises ValueError."""
        import pytest

        from app.handlers import _parse_yyyy_mm_dd

        with pytest.raises(ValueError):
            _parse_yyyy_mm_dd("not-a-date")

    def test_iter_inclusive_dates_single_day(self):
        """Test date iteration with single day (start == end)."""
        from app.handlers import _iter_inclusive_dates

        start = date(2024, 1, 15)
        end = date(2024, 1, 15)
        result = _iter_inclusive_dates(start, end)

        assert len(result) == 1
        assert result[0] == date(2024, 1, 15)

    def test_iter_inclusive_dates_multiple_days(self):
        """Test date iteration with multiple days."""
        from app.handlers import _iter_inclusive_dates

        start = date(2024, 1, 15)
        end = date(2024, 1, 17)
        result = _iter_inclusive_dates(start, end)

        assert len(result) == 3
        assert result[0] == date(2024, 1, 15)
        assert result[1] == date(2024, 1, 16)
        assert result[2] == date(2024, 1, 17)

    def test_iter_inclusive_dates_start_after_end(self):
        """Test date iteration raises ValueError when start > end."""
        import pytest

        from app.handlers import _iter_inclusive_dates

        start = date(2024, 1, 20)
        end = date(2024, 1, 15)

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            _iter_inclusive_dates(start, end)
