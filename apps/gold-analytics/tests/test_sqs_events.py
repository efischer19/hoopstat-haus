"""
Tests for SQS event handling in Gold Analytics Lambda handlers.

Tests the normalize_event function to ensure it properly handles both
direct S3 events and SQS-wrapped S3 events.
"""

import json
import pytest

from gold_analytics.app.handlers import normalize_event


class TestGoldAnalyticsEventNormalization:
    """Test event normalization for SQS and direct S3 events in Gold Analytics."""

    def test_normalize_direct_s3_event(self):
        """Test normalization of direct S3 events (no change expected)."""
        direct_s3_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "silver-bucket"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/data.parquet"}
                    }
                }
            ]
        }
        
        result = normalize_event(direct_s3_event)
        
        # Should return the same event structure
        assert result == direct_s3_event
        assert len(result["Records"]) == 1
        assert result["Records"][0]["eventSource"] == "aws:s3"

    def test_normalize_sqs_wrapped_silver_event(self):
        """Test normalization of SQS-wrapped Silver layer S3 events."""
        s3_event_body = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/data.parquet"}
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
        assert "silver" in result["Records"][0]["s3"]["object"]["key"]

    def test_normalize_multiple_silver_files_from_sqs(self):
        """Test normalization with multiple Silver files from SQS."""
        s3_event_1 = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/game_123.parquet"}
                    }
                }
            ]
        }
        
        s3_event_2 = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/team_stats/season=2024-25/date=2024-01-15/game_123.parquet"}
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
        assert "player_stats" in result["Records"][0]["s3"]["object"]["key"]
        assert "team_stats" in result["Records"][1]["s3"]["object"]["key"]

    def test_normalize_batch_processing_scenario(self):
        """Test a realistic batch processing scenario."""
        # Simulate multiple parquet files created at once
        s3_batch_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/part_001.parquet"}
                    }
                },
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/part_002.parquet"}
                    }
                },
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/team_stats/season=2024-25/date=2024-01-15/summary.parquet"}
                    }
                }
            ]
        }
        
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(s3_batch_event)
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should handle batch of S3 events properly
        assert "Records" in result
        assert len(result["Records"]) == 3
        assert all("silver/" in record["s3"]["object"]["key"] for record in result["Records"])
        assert all(".parquet" in record["s3"]["object"]["key"] for record in result["Records"])

    def test_normalize_error_resilience(self):
        """Test that one bad SQS message doesn't break processing of good ones."""
        good_s3_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "hoopstat-haus-silver"},
                        "object": {"key": "silver/player_stats/season=2024-25/date=2024-01-15/data.parquet"}
                    }
                }
            ]
        }
        
        sqs_event = {
            "Records": [
                {
                    "eventSource": "aws:sqs",
                    "body": "corrupted json data ["
                },
                {
                    "eventSource": "aws:sqs",
                    "body": json.dumps(good_s3_event)
                },
                {
                    "eventSource": "aws:sqs",
                    "body": ""  # Empty body
                }
            ]
        }
        
        result = normalize_event(sqs_event)
        
        # Should process the one good message and skip the bad ones
        assert "Records" in result
        assert len(result["Records"]) == 1
        assert result["Records"][0]["s3"]["bucket"]["name"] == "hoopstat-haus-silver"