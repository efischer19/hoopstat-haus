"""Tests for the Lambda handlers module."""

import pytest

from app.handlers import lambda_handler, parse_s3_events, process_s3_record
from app.processors import SilverProcessor


class TestLambdaHandler:
    """Test cases for Lambda event handlers."""

    def test_lambda_handler_empty_event(self):
        """Test Lambda handler with empty event."""
        event = {}
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 200
        assert "No records to process" in result["message"]

    def test_lambda_handler_no_s3_records(self):
        """Test Lambda handler with non-S3 records."""
        event = {"Records": [{"eventSource": "aws:sns"}]}
        context = {}
        result = lambda_handler(event, context)
        assert result["statusCode"] == 200

    def test_parse_s3_events_empty(self):
        """Test parsing empty S3 events."""
        event = {}
        records = parse_s3_events(event)
        assert records == []

    def test_parse_s3_events_with_s3_records(self):
        """Test parsing S3 events with valid records."""
        event = {
            "Records": [
                {"eventSource": "aws:s3", "s3": {"bucket": {"name": "test"}}},
                {"eventSource": "aws:sns"},  # Should be filtered out
                {"eventSource": "aws:s3", "s3": {"bucket": {"name": "test2"}}},
            ]
        }
        records = parse_s3_events(event)
        assert len(records) == 2
        assert all(r["eventSource"] == "aws:s3" for r in records)

    def test_process_s3_record_valid(self):
        """Test processing a valid S3 record."""
        processor = SilverProcessor()
        record = {
            "s3": {
                "bucket": {"name": "test-bucket"},
                "object": {"key": "test/key.json"},
            }
        }
        result = process_s3_record(processor, record)
        assert result["success"] is True
        assert result["record"]["bucket"] == "test-bucket"
        assert result["record"]["key"] == "test/key.json"

    def test_process_s3_record_missing_bucket(self):
        """Test processing S3 record with missing bucket."""
        processor = SilverProcessor()
        record = {"s3": {"object": {"key": "test/key.json"}}}
        with pytest.raises(ValueError, match="Missing S3 bucket or key"):
            process_s3_record(processor, record)
