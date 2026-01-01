"""
Tests for SilverS3Manager functionality.
"""

import json
from datetime import date
from unittest.mock import patch

import pytest
from moto import mock_aws

from hoopstat_s3 import SilverS3Manager, SilverS3ManagerError


class TestSilverS3Manager:
    """Test cases for SilverS3Manager."""

    @mock_aws
    def test_init_with_mocked_s3(self):
        """Test SilverS3Manager initialization with mocked S3."""
        # Create mock S3 bucket
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager(bucket_name="test-bucket", region_name="us-east-1")

        assert manager.bucket_name == "test-bucket"
        assert manager.region_name == "us-east-1"
        assert manager.s3_client is not None

    def test_init_with_invalid_bucket(self):
        """Test SilverS3Manager initialization with invalid bucket."""
        from hoopstat_s3 import S3UploadError

        with pytest.raises(S3UploadError):
            SilverS3Manager(
                bucket_name="nonexistent-bucket-12345", region_name="us-east-1"
            )

    @mock_aws
    def test_read_bronze_json_success(self):
        """Test successful Bronze JSON data reading."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create test Bronze data
        test_data = {"game_id": 123, "teams": ["Lakers", "Celtics"]}
        s3_client.put_object(
            Bucket="test-bucket",
            Key="raw/box/2024-01-15/data.json",
            Body=json.dumps(test_data).encode("utf-8"),
            ContentType="application/json",
        )

        manager = SilverS3Manager("test-bucket")
        target_date = date(2024, 1, 15)

        result = manager.read_bronze_json("box", target_date)

        assert result is not None
        assert result == test_data

    @mock_aws
    def test_read_bronze_json_not_found(self):
        """Test Bronze JSON reading when data doesn't exist."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")
        target_date = date(2024, 1, 15)

        result = manager.read_bronze_json("box", target_date)

        assert result is None

    @mock_aws
    def test_read_bronze_json_invalid_json(self):
        """Test Bronze JSON reading with invalid JSON content."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create invalid JSON data
        s3_client.put_object(
            Bucket="test-bucket",
            Key="raw/box/2024-01-15/data.json",
            Body=b"invalid json content",
            ContentType="application/json",
        )

        manager = SilverS3Manager("test-bucket")
        target_date = date(2024, 1, 15)

        with pytest.raises(SilverS3ManagerError):
            manager.read_bronze_json("box", target_date)

    @mock_aws
    def test_write_silver_json_success(self):
        """Test successful Silver JSON data writing."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        test_data = [
            {"player_id": "123", "points": 25, "rebounds": 10},
            {"player_id": "456", "points": 18, "rebounds": 7},
        ]
        target_date = date(2024, 1, 15)

        result_key = manager.write_silver_json(
            "player-stats", test_data, target_date, check_exists=False
        )

        expected_key = "silver/player-stats/2024-01-15/players.json"
        assert result_key == expected_key

        # Verify data was written correctly
        response = s3_client.get_object(Bucket="test-bucket", Key=expected_key)
        written_data = json.loads(response["Body"].read().decode("utf-8"))
        assert written_data == test_data

        # Verify metadata
        metadata = response["Metadata"]
        assert metadata["data_layer"] == "silver"
        assert metadata["entity_type"] == "player-stats"
        assert metadata["format"] == "json"

    @mock_aws
    def test_write_silver_json_with_idempotency_check(self):
        """Test Silver JSON writing with idempotency check."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        test_data = [{"player_id": "123", "points": 25}]
        target_date = date(2024, 1, 15)

        # First write
        result_key1 = manager.write_silver_json("player-stats", test_data, target_date)

        # Second write with idempotency check (should skip)
        result_key2 = manager.write_silver_json(
            "player-stats", test_data, target_date, check_exists=True
        )

        assert result_key1 == result_key2

    @mock_aws
    def test_write_partitioned_silver_data(self):
        """Test writing partitioned Silver data for all entity types."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        silver_data = {
            "player-stats": [{"player_id": "123", "points": 25}],
            "team-stats": [{"team_id": "1", "score": 108}],
            "game-stats": [{"game_id": "12345", "home_score": 108, "away_score": 95}],
        }
        target_date = date(2024, 1, 15)

        results = manager.write_partitioned_silver_data(
            silver_data, target_date, check_exists=False
        )

        assert len(results) == 3
        assert "player-stats" in results
        assert "team-stats" in results
        assert "game-stats" in results

        # Verify all files were created
        expected_keys = [
            "silver/player-stats/2024-01-15/players.json",
            "silver/team-stats/2024-01-15/teams.json",
            "silver/game-stats/2024-01-15/games.json",
        ]

        for key in expected_keys:
            response = s3_client.get_object(Bucket="test-bucket", Key=key)
            assert response is not None

    @mock_aws
    def test_write_partitioned_silver_data_with_empty_lists(self):
        """Test writing partitioned Silver data with some empty lists."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        silver_data = {
            "player_stats": [{"player_id": "123", "points": 25}],
            "team_stats": [],  # Empty list
            "game_stats": [{"game_id": "12345", "home_score": 108}],
        }
        target_date = date(2024, 1, 15)

        results = manager.write_partitioned_silver_data(
            silver_data, target_date, check_exists=False
        )

        # Should only write non-empty data
        assert len(results) == 2
        assert "player_stats" in results
        assert "team_stats" not in results
        assert "game_stats" in results

    @mock_aws
    def test_parse_s3_event_with_bronze_triggers(self):
        """Test parsing S3 events for Bronze layer triggers."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        test_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "raw/box/2024-01-15/data.json"},
                    },
                },
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {
                            "key": "silver/player-stats/2024-01-15/players.json"
                        },  # Should be ignored
                    },
                },
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "raw/standings/2024-01-16/data.json"},
                    },
                },
            ]
        }

        bronze_events = manager.parse_s3_event(test_event)

        assert len(bronze_events) == 2

        # First event
        assert bronze_events[0]["entity"] == "box"
        assert bronze_events[0]["date"] == date(2024, 1, 15)
        assert bronze_events[0]["bucket"] == "test-bucket"

        # Second event
        assert bronze_events[1]["entity"] == "standings"
        assert bronze_events[1]["entity"] == "standings"
        assert bronze_events[1]["date"] == date(2024, 1, 16)

    @mock_aws
    def test_parse_s3_event_with_no_bronze_triggers(self):
        """Test parsing S3 events with no Bronze layer triggers."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        test_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {
                            "key": "silver/player-stats/2024-01-15/players.json"
                        },
                    },
                },
                {
                    "eventSource": "aws:lambda",  # Not S3
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "raw/box/2024-01-15/data.json"},
                    },
                },
            ]
        }

        bronze_events = manager.parse_s3_event(test_event)

        assert len(bronze_events) == 0

    @mock_aws
    def test_is_bronze_trigger_event(self):
        """Test Bronze trigger event detection."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        # Valid Bronze events (new format without 'date=')
        assert (
            manager._is_bronze_trigger_event("raw/box/2024-01-15/data.json")
            is True
        )
        assert (
            manager._is_bronze_trigger_event("raw/standings/2024-12-25/data.json")
            is True
        )

        # Invalid events
        assert (
            manager._is_bronze_trigger_event(
                "silver/player-stats/2024-01-15/players.json"
            )
            is False
        )
        assert (
            manager._is_bronze_trigger_event("raw/box_scores/data.json") is False
        )  # No date
        assert (
            manager._is_bronze_trigger_event(
                "raw/box/2024-01-15/0022500123.json"
            )
            is True
        )  # Game ID filename

        assert (
            manager._is_bronze_trigger_event("raw/box/2024-01-15/data.txt")
            is False
        )  # Not .json
        assert (
            manager._is_bronze_trigger_event(
                "processed/box/2024-01-15/data.json"
            )
            is False
        )  # Not raw

    @mock_aws
    def test_extract_entity_info_from_key(self):
        """Test entity information extraction from S3 keys."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        # Valid key
        result = manager._extract_entity_info_from_key(
            "raw/box/2024-01-15/data.json"
        )
        assert result is not None
        assert result["entity"] == "box"
        assert result["date"] == date(2024, 1, 15)
        assert result["date_str"] == "2024-01-15"

        # Invalid keys
        assert (
            manager._extract_entity_info_from_key(
                "silver/player-stats/2024-01-15/players.json"
            )
            is None
        )
        assert manager._extract_entity_info_from_key("raw/box/data.json") is None
        assert (
            manager._extract_entity_info_from_key(
                "raw/box/invalid/data.json"
            )
            is None
        )

    @mock_aws
    def test_list_bronze_data(self):
        """Test listing Bronze data."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create test Bronze data files
        test_files = [
            "raw/box/2024-01-15/data.json",
            "raw/box/2024-01-16/data.json",
            "raw/box/2024-01-17/data.json",
        ]

        for key in test_files:
            s3_client.put_object(
                Bucket="test-bucket",
                Key=key,
                Body=json.dumps({"test": "data"}).encode("utf-8"),
            )

        manager = SilverS3Manager("test-bucket")

        # List all Bronze data for box_scores
        bronze_data = manager.list_bronze_data("box")

        assert len(bronze_data) == 3
        assert all(item["entity"] == "box" for item in bronze_data)

        # Verify dates are parsed correctly
        dates = [item["date"] for item in bronze_data]
        expected_dates = [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17)]
        assert dates == expected_dates

    @mock_aws
    def test_list_bronze_data_with_date_filter(self):
        """Test listing Bronze data with date filtering."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create test Bronze data files
        test_files = [
            "raw/box/2024-01-15/data.json",
            "raw/box/2024-01-16/data.json",
            "raw/box/2024-01-17/data.json",
        ]

        for key in test_files:
            s3_client.put_object(
                Bucket="test-bucket",
                Key=key,
                Body=json.dumps({"test": "data"}).encode("utf-8"),
            )

        manager = SilverS3Manager("test-bucket")

        # List Bronze data with date filter
        bronze_data = manager.list_bronze_data(
            "box", start_date=date(2024, 1, 16), end_date=date(2024, 1, 16)
        )

        assert len(bronze_data) == 1
        assert bronze_data[0]["date"] == date(2024, 1, 16)

    @mock_aws
    def test_list_silver_data(self):
        """Test listing Silver data."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create test Silver data files
        test_files = [
            "silver/player-stats/2024-01-15/players.json",
            "silver/player-stats/2024-01-16/players.json",
            "silver/team-stats/2024-01-15/teams.json",
        ]

        for key in test_files:
            s3_client.put_object(
                Bucket="test-bucket",
                Key=key,
                Body=json.dumps([{"test": "data"}]).encode("utf-8"),
            )

        manager = SilverS3Manager("test-bucket")

        # List Silver data for player_stats
        silver_data = manager.list_silver_data("player-stats")

        assert len(silver_data) == 2
        assert all(item["entity_type"] == "player-stats" for item in silver_data)

        # Verify dates are parsed correctly
        dates = [item["date"] for item in silver_data]
        expected_dates = [date(2024, 1, 15), date(2024, 1, 16)]
        assert dates == expected_dates

    @mock_aws
    def test_list_silver_data_with_date_filter(self):
        """Test listing Silver data with date filtering."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        # Create test Silver data files
        test_files = [
            "silver/player-stats/2024-01-15/players.json",
            "silver/player-stats/2024-01-16/players.json",
            "silver/player-stats/2024-01-17/players.json",
        ]

        for key in test_files:
            s3_client.put_object(
                Bucket="test-bucket",
                Key=key,
                Body=json.dumps([{"test": "data"}]).encode("utf-8"),
            )

        manager = SilverS3Manager("test-bucket")

        # List Silver data with date filter
        silver_data = manager.list_silver_data(
            "player-stats", start_date=date(2024, 1, 16), end_date=date(2024, 1, 16)
        )

        assert len(silver_data) == 1
        assert silver_data[0]["date"] == date(2024, 1, 16)

    @mock_aws
    def test_silver_data_exists_check(self):
        """Test checking if Silver data exists."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        test_key = "silver/player-stats/2024-01-15/players.json"

        # Initially should not exist
        assert manager._silver_data_exists(test_key) is False

        # Create the object
        s3_client.put_object(
            Bucket="test-bucket",
            Key=test_key,
            Body=json.dumps([{"test": "data"}]).encode("utf-8"),
        )

        # Now should exist
        assert manager._silver_data_exists(test_key) is True

    @mock_aws
    def test_entity_filename_mapping(self):
        """Test entity type to filename mapping."""
        # Setup mock S3
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        manager = SilverS3Manager("test-bucket")

        # Test all supported entity types through write_silver_json
        # (without actually writing)
        with patch.object(manager, "_upload_to_s3") as mock_upload:
            mock_upload.return_value = None

            with patch.object(manager, "_silver_data_exists") as mock_exists:
                mock_exists.return_value = False

                target_date = date(2024, 1, 15)

                # Test player_stats -> players.json
                key1 = manager.write_silver_json(
                    "player-stats", [], target_date, check_exists=False
                )
                assert key1 == "silver/player-stats/2024-01-15/players.json"

                # Test team_stats -> teams.json
                key2 = manager.write_silver_json(
                    "team-stats", [], target_date, check_exists=False
                )
                assert key2 == "silver/team-stats/2024-01-15/teams.json"

                # Test game_stats -> games.json
                key3 = manager.write_silver_json(
                    "game-stats", [], target_date, check_exists=False
                )
                assert key3 == "silver/game-stats/2024-01-15/games.json"

                # Test custom entity type
                key4 = manager.write_silver_json(
                    "custom-stats", [], target_date, check_exists=False
                )
                assert key4 == "silver/custom-stats/2024-01-15/custom-stats.json"
