"""Tests for the quarantine module."""

import json
from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest

from app.quarantine import DataQuarantine


class TestDataQuarantine:
    """Test the DataQuarantine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_s3_manager = Mock()
        self.mock_s3_manager.bucket_name = "test-bucket"
        self.mock_s3_manager.s3_client = Mock()
        self.quarantine = DataQuarantine(self.mock_s3_manager)

    def test_quarantine_data_success(self):
        """Test successful data quarantining."""
        test_data = {"invalid": "data"}
        validation_result = {
            "valid": False,
            "issues": ["Schema validation failed"],
            "metrics": {"schema_valid": False},
        }

        with patch("app.quarantine.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 12, 25, 10, 30, 0)

            quarantine_key = self.quarantine.quarantine_data(
                test_data, validation_result, "schedule", date(2023, 12, 25)
            )

        # Check that S3 put_object was called
        self.mock_s3_manager.s3_client.put_object.assert_called_once()

        # Verify the quarantine key format
        assert "quarantine/year=2023/month=12/day=25" in quarantine_key
        assert "schedule" in quarantine_key
        assert quarantine_key.endswith(".json")

    def test_quarantine_api_response(self):
        """Test quarantining API response with context."""
        response_data = {"api": "response", "invalid": True}
        validation_result = {
            "valid": False,
            "issues": ["API validation failed"],
        }

        quarantine_key = self.quarantine.quarantine_api_response(
            response_data,
            validation_result,
            "get_games_for_date",
            date(2023, 12, 25),
            {"param1": "value1"},
        )

        # Should call quarantine_data with proper context
        assert quarantine_key.startswith("quarantine/")

    def test_generate_quarantine_key(self):
        """Test quarantine key generation."""
        timestamp = datetime(2023, 12, 25, 10, 30, 45, 123456)
        target_date = date(2023, 12, 25)

        key = self.quarantine._generate_quarantine_key(
            "schedule", target_date, timestamp
        )

        expected = (
            "quarantine/year=2023/month=12/day=25/schedule/"
            "quarantine_20231225_103045_123456.json"
        )
        assert key == expected

    def test_store_quarantine_record(self):
        """Test storing quarantine record in S3."""
        record = {
            "data": {"test": "data"},
            "validation_result": {"valid": False},
            "metadata": {
                "data_type": "schedule",
                "issues_count": 1,
            },
        }
        key = "test/quarantine/key.json"

        self.quarantine._store_quarantine_record(record, key)

        # Verify S3 put_object call
        self.mock_s3_manager.s3_client.put_object.assert_called_once()
        call_args = self.mock_s3_manager.s3_client.put_object.call_args

        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == key
        assert call_args[1]["ContentType"] == "application/json"

        # Verify the body is valid JSON
        body = call_args[1]["Body"].decode("utf-8")
        parsed = json.loads(body)
        assert parsed["data"]["test"] == "data"

    def test_store_quarantine_record_s3_error(self):
        """Test handling S3 errors during quarantine storage."""
        self.mock_s3_manager.s3_client.put_object.side_effect = Exception("S3 Error")

        record = {
            "data": {"test": "data"},
            "validation_result": {"valid": False},
            "metadata": {
                "data_type": "schedule",
                "issues_count": 1,
            },
        }
        key = "test/key.json"

        with pytest.raises(Exception, match="S3 Error"):
            self.quarantine._store_quarantine_record(record, key)

    def test_list_quarantined_data_success(self):
        """Test listing quarantined data."""
        mock_response = {
            "Contents": [
                {
                    "Key": "quarantine/year=2023/month=12/day=25/schedule/file1.json",
                    "Size": 1024,
                    "LastModified": datetime(2023, 12, 25, 10, 0, 0),
                    "Metadata": {"data_type": "schedule"},
                },
                {
                    "Key": "quarantine/year=2023/month=12/day=25/box_score/file2.json",
                    "Size": 2048,
                    "LastModified": datetime(2023, 12, 25, 11, 0, 0),
                    "Metadata": {"data_type": "box_score"},
                },
            ]
        }

        self.mock_s3_manager.s3_client.list_objects_v2.return_value = mock_response

        result = self.quarantine.list_quarantined_data(date(2023, 12, 25))

        assert len(result) == 2
        assert (
            result[0]["key"]
            == "quarantine/year=2023/month=12/day=25/schedule/file1.json"
        )
        assert result[0]["size"] == 1024
        assert (
            result[1]["key"]
            == "quarantine/year=2023/month=12/day=25/box_score/file2.json"
        )

    def test_list_quarantined_data_with_filters(self):
        """Test listing quarantined data with date and type filters."""
        target_date = date(2023, 12, 25)
        data_type = "schedule"

        self.mock_s3_manager.s3_client.list_objects_v2.return_value = {"Contents": []}

        self.quarantine.list_quarantined_data(target_date, data_type)

        # Verify the prefix includes date and type filters
        call_args = self.mock_s3_manager.s3_client.list_objects_v2.call_args
        prefix = call_args[1]["Prefix"]

        assert "year=2023" in prefix
        assert "month=12" in prefix
        assert "day=25" in prefix
        assert "schedule" in prefix

    def test_list_quarantined_data_s3_error(self):
        """Test handling S3 errors when listing quarantined data."""
        self.mock_s3_manager.s3_client.list_objects_v2.side_effect = Exception(
            "S3 Error"
        )

        result = self.quarantine.list_quarantined_data()

        assert result == []

    def test_get_quarantine_summary(self):
        """Test getting quarantine summary statistics."""
        mock_items = [
            {
                "key": "quarantine/year=2023/month=12/day=25/schedule/file1.json",
                "last_modified": "2023-12-25T10:00:00",
            },
            {
                "key": "quarantine/year=2023/month=12/day=25/box_score/file2.json",
                "last_modified": "2023-12-25T11:00:00",
            },
        ]

        with patch.object(
            self.quarantine, "list_quarantined_data", return_value=mock_items
        ):
            summary = self.quarantine.get_quarantine_summary()

        assert summary["total_quarantined"] == 2
        assert "schedule" in summary["by_data_type"]
        assert "box_score" in summary["by_data_type"]
        assert summary["by_data_type"]["schedule"] == 1
        assert summary["by_data_type"]["box_score"] == 1
        assert len(summary["recent_items"]) == 2

    def test_get_quarantine_summary_error(self):
        """Test error handling in quarantine summary."""
        with patch.object(
            self.quarantine, "list_quarantined_data", side_effect=Exception("Error")
        ):
            summary = self.quarantine.get_quarantine_summary()

        assert summary["total_quarantined"] == 0
        assert "error" in summary

    def test_should_quarantine_invalid_data(self):
        """Test quarantine decision for invalid data."""
        validation_result = {
            "valid": False,
            "issues": ["Schema validation failed"],
        }

        should_quarantine = self.quarantine.should_quarantine(validation_result)
        assert should_quarantine is True

    def test_should_quarantine_valid_data(self):
        """Test quarantine decision for valid data."""
        validation_result = {
            "valid": True,
            "issues": [],
        }

        should_quarantine = self.quarantine.should_quarantine(validation_result)
        assert should_quarantine is False

    def test_should_quarantine_critical_issues(self):
        """Test quarantine decision for data with critical issues."""
        validation_result = {
            "valid": True,  # Passed validation but has critical issues
            "issues": ["Missing critical field", "Schema inconsistency detected"],
        }

        should_quarantine = self.quarantine.should_quarantine(validation_result)
        assert should_quarantine is True

    def test_quarantine_data_exception_handling(self):
        """Test exception handling during quarantine process."""
        self.mock_s3_manager.s3_client.put_object.side_effect = Exception("S3 Error")

        test_data = {"invalid": "data"}
        validation_result = {"valid": False, "issues": ["Test error"]}

        # Should not raise exception, but return error key
        quarantine_key = self.quarantine.quarantine_data(
            test_data, validation_result, "schedule", date(2023, 12, 25)
        )

        assert "quarantine_failed" in quarantine_key
