"""Tests for the Lambda handlers module."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.handlers import lambda_handler, process_bronze_event
from app.processors import SilverProcessor


class TestLambdaHandler:
    """Test cases for Lambda event handlers."""

    @patch('app.handlers.SilverS3Manager')
    @patch.dict('os.environ', {'BRONZE_BUCKET': 'test-bucket'})
    def test_lambda_handler_empty_event(self, mock_s3_manager):
        """Test Lambda handler with empty event."""
        # Mock S3 manager to return no Bronze events
        mock_manager = MagicMock()
        mock_manager.parse_s3_event.return_value = []
        mock_s3_manager.return_value = mock_manager
        
        event = {}
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 200
        assert "No Bronze triggers to process" in result["message"]

    @patch.dict('os.environ', {}, clear=True)
    def test_lambda_handler_no_bucket_configured(self):
        """Test Lambda handler with no bucket configured."""
        event = {}
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 400
        assert "No bucket configured" in result["message"]

    @patch('app.handlers.SilverS3Manager')
    @patch.dict('os.environ', {'BRONZE_BUCKET': 'test-bucket'})
    def test_lambda_handler_with_bronze_events(self, mock_s3_manager):
        """Test Lambda handler with Bronze trigger events."""
        # Mock S3 manager to return Bronze events
        mock_manager = MagicMock()
        mock_bronze_event = {
            "bucket": "test-bucket",
            "key": "raw/box_scores/date=2024-01-15/data.json",
            "entity": "box_scores",
            "date": date(2024, 1, 15)
        }
        mock_manager.parse_s3_event.return_value = [mock_bronze_event]
        mock_s3_manager.return_value = mock_manager
        
        # Mock the processor to succeed
        with patch('app.handlers.SilverProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_date.return_value = True
            mock_processor_class.return_value = mock_processor
            
            event = {"Records": [{"eventSource": "aws:s3"}]}
            context = {}
            result = lambda_handler(event, context)
            
            assert result["statusCode"] == 200
            assert "Processed 1/1 Bronze events" in result["message"]

    def test_process_bronze_event_valid(self):
        """Test processing a valid Bronze event."""
        # Mock processor
        processor = MagicMock()
        processor.process_date.return_value = True
        
        bronze_event = {
            "bucket": "test-bucket",
            "key": "raw/box_scores/date=2024-01-15/data.json",
            "entity": "box_scores",
            "date": date(2024, 1, 15)
        }
        
        result = process_bronze_event(processor, bronze_event)
        assert result["success"] is True
        assert result["bronze_event"]["entity"] == "box_scores"
        assert "Successfully processed" in result["message"]

    def test_process_bronze_event_missing_info(self):
        """Test processing Bronze event with missing information."""
        processor = MagicMock()
        bronze_event = {"bucket": "test-bucket"}  # Missing required fields
        
        with pytest.raises(ValueError, match="Missing required Bronze event information"):
            process_bronze_event(processor, bronze_event)

    def test_process_bronze_event_processing_failure(self):
        """Test processing Bronze event when processing fails."""
        # Mock processor to fail
        processor = MagicMock()
        processor.process_date.return_value = False
        
        bronze_event = {
            "bucket": "test-bucket",
            "key": "raw/box_scores/date=2024-01-15/data.json",
            "entity": "box_scores",
            "date": date(2024, 1, 15)
        }
        
        result = process_bronze_event(processor, bronze_event)
        assert result["success"] is False
        assert "Processing failed" in result["message"]
