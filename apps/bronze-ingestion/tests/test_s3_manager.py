"""Tests for the S3 manager module."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from app.s3_manager import BronzeS3Manager


class TestBronzeS3Manager:
    """Test the Bronze S3 manager functionality."""

    @patch("app.s3_manager.boto3.client")
    def test_init_success(self, mock_boto_client):
        """Test successful S3 manager initialization."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket", "us-west-2")

        assert manager.bucket_name == "test-bucket"
        assert manager.region_name == "us-west-2"
        mock_boto_client.assert_called_once_with("s3", region_name="us-west-2")

    @patch("app.s3_manager.boto3.client")
    def test_check_exists_true(self, mock_boto_client):
        """Test checking if data exists returns True."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {"KeyCount": 1}
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        target_date = date(2023, 12, 25)
        exists = manager.check_exists("games", target_date)

        assert exists is True
        mock_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="raw/games/date=2023-12-25/", MaxKeys=1
        )

    @patch("app.s3_manager.boto3.client")
    def test_check_exists_false(self, mock_boto_client):
        """Test checking if data exists returns False."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        target_date = date(2023, 12, 25)
        exists = manager.check_exists("games", target_date)

        assert exists is False

    @patch("app.s3_manager.boto3.client")
    def test_list_entities_for_date(self, mock_boto_client):
        """Test listing entities that have data for a date."""
        mock_client = Mock()

        # Mock the response for listing prefixes
        mock_client.list_objects_v2.side_effect = [
            # First call - list all entities
            {
                "CommonPrefixes": [
                    {"Prefix": "raw/games/"},
                    {"Prefix": "raw/box_scores/"},
                    {"Prefix": "raw/schedule/"},
                ]
            },
            # Subsequent calls - check if each entity has data for the date
            {"KeyCount": 1},  # games has data
            {"KeyCount": 0},  # box_scores has no data
            {"KeyCount": 1},  # schedule has data
        ]
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        target_date = date(2023, 12, 25)
        entities = manager.list_entities_for_date(target_date)

        # Should return entities that have data
        assert entities == ["games", "schedule"]

        # Verify the calls
        assert mock_client.list_objects_v2.call_count == 4

    @patch("app.s3_manager.boto3.client")
    def test_store_json(self, mock_boto_client):
        """Test storing dictionary as JSON."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        # Create test data
        test_data = {
            "game_id": "12345",
            "teams": ["LAL", "GSW"],
            "scores": [100, 95],
            "metadata": {"venue": "Staples Center", "attendance": 18997},
        }

        target_date = date(2023, 12, 25)

        # Store the JSON data
        key = manager.store_json(test_data, "games", target_date)

        # Verify the key structure (no game_id, uses data.json)
        expected_key = "raw/games/date=2023-12-25/data.json"
        assert key == expected_key

        # Verify S3 put_object was called
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args

        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == expected_key
        assert call_args[1]["ContentType"] == "application/json"

        # Verify metadata
        metadata = call_args[1]["Metadata"]
        assert metadata["entity"] == "games"
        assert metadata["date"] == "2023-12-25"
        assert metadata["format"] == "json"

        # Verify the JSON content
        body = call_args[1]["Body"]
        # Decode bytes and parse JSON to verify it's valid
        import json

        parsed_data = json.loads(body.decode("utf-8"))
        assert parsed_data["game_id"] == "12345"
        assert parsed_data["teams"] == ["LAL", "GSW"]
        assert parsed_data["metadata"]["venue"] == "Staples Center"

    @patch("app.s3_manager.boto3.client")
    def test_store_json_with_game_id(self, mock_boto_client):
        """Test storing dictionary as JSON with game_id (ADR-031)."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        # Create test data
        test_data = {
            "game_id": "0022400123",
            "teams": ["LAL", "GSW"],
            "scores": [100, 95],
        }

        target_date = date(2023, 12, 25)

        # Store the JSON data with game_id
        key = manager.store_json(
            test_data, "box_scores", target_date, game_id="0022400123"
        )

        # Verify the key structure uses game_id as filename
        expected_key = "raw/box_scores/date=2023-12-25/0022400123.json"
        assert key == expected_key

        # Verify S3 put_object was called with correct key
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args

        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == expected_key
        assert call_args[1]["ContentType"] == "application/json"

    @patch("app.s3_manager.boto3.client")
    def test_store_json_s3_error(self, mock_boto_client):
        """Test handling of S3 errors during JSON storage."""
        mock_client = Mock()
        mock_client.put_object.side_effect = Exception("S3 JSON Error")
        mock_boto_client.return_value = mock_client

        manager = BronzeS3Manager("test-bucket")

        test_data = {"test": "data"}
        target_date = date(2023, 12, 25)

        # Should raise exception
        with pytest.raises(Exception, match="S3 JSON Error"):
            manager.store_json(test_data, "test", target_date)
