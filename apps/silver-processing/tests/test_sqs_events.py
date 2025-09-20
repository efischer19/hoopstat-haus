"""
Tests for SQS event handling in Lambda handlers.

Tests the normalize_event function to ensure it properly handles both
direct S3 events and SQS-wrapped S3 events.
"""

import json
import pytest

from silver_processing.app.handlers import normalize_event


class TestEventNormalization:
    """Test event normalization for SQS and direct S3 events."""

    def test_normalize_direct_s3_event(self):
        """Test normalization of direct S3 events (no change expected)."""
        direct_s3_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test/file.json"}
                    }
                }
            ]
        }
        
        result = normalize_event(direct_s3_event)
        
        # Should return the same event structure
        assert result == direct_s3_event
        assert len(result["Records"]) == 1
        assert result["Records"][0]["eventSource"] == "aws:s3"

    def test_normalize_sqs_wrapped_s3_event(self):
        """Test normalization of SQS-wrapped S3 events."""
        s3_event_body = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test/file.json"}
                    }
                }
            ]
        }
        
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(s3_event_body)
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should extract and return the S3 events from SQS body
        assert "Records" in result
        assert len(result["Records"]) == 1
        assert result["Records"][0]["eventSource"] == "aws:s3"
        assert result["Records"][0]["s3"]["bucket"]["name"] == "test-bucket"

    def test_normalize_multiple_sqs_messages(self):
        """Test normalization with multiple SQS messages containing S3 events."""
        s3_event_1 = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "bucket1"},
                        "object": {"key": "file1.json"}
                    }
                }
            ]
        }
        
        s3_event_2 = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "bucket2"},
                        "object": {"key": "file2.json"}
                    }
                }
            ]
        }
        
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(s3_event_1)
                },
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(s3_event_2)
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should extract all S3 events from all SQS messages
        assert "Records" in result
        assert len(result["Records"]) == 2
        assert result["Records"][0]["s3"]["object"]["key"] == "file1.json"
        assert result["Records"][1]["s3"]["object"]["key"] == "file2.json"

    def test_normalize_sqs_event_with_invalid_json(self):
        """Test handling of SQS events with invalid JSON in body."""
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": "invalid json content"
                },
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps({
                        "Records": [
                            {
                                "eventSource": "aws:s3",
                                "s3": {
                                    "bucket": {"name": "valid-bucket"},
                                    "object": {"key": "valid-file.json"}
                                }
                            }
                        ]
                    })
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should skip invalid JSON and process valid messages
        assert "Records" in result
        assert len(result["Records"]) == 1
        assert result["Records"][0]["s3"]["bucket"]["name"] == "valid-bucket"

    def test_normalize_empty_event(self):
        """Test handling of empty or malformed events."""
        empty_event = {}
        result = normalize_event(empty_event)
        assert result == empty_event
        
        no_records_event = {"Records": []}
        result = normalize_event(no_records_event)
        assert result == no_records_event

    def test_normalize_unknown_event_source(self):
        """Test handling of events with unknown event sources."""
        unknown_event = {
            "Records": [
                {
                    "eventSource": "aws:unknown",
                    "data": "some data"
                }
            ]
        }
        
        result = normalize_event(unknown_event)
        
        # Should return the event unchanged with a warning
        assert result == unknown_event

    def test_normalize_sqs_event_with_multiple_s3_records(self):
        """Test SQS message containing multiple S3 records in a single body."""
        s3_event_with_multiple_records = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "bucket1"},
                        "object": {"key": "file1.json"}
                    }
                },
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "bucket1"},
                        "object": {"key": "file2.json"}
                    }
                }
            ]
        }
        
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(s3_event_with_multiple_records)
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should extract all S3 records from the single SQS message
        assert "Records" in result
        assert len(result["Records"]) == 2
        assert all(record["eventSource"] == "aws:s3" for record in result["Records"])