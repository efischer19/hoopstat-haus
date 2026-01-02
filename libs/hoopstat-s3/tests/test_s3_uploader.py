"""
Tests for the S3 uploader functionality.
"""

from datetime import date
from unittest.mock import Mock, patch

import boto3
import pytest
from moto import mock_aws

from hoopstat_s3.s3_uploader import S3Uploader, S3UploadError


class TestS3Uploader:
    """Test cases for S3Uploader class."""

    @mock_aws
    def test_init_with_mocked_s3(self):
        """Test initialization with mocked S3."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")
        assert uploader.bucket_name == "test-bucket"

    def test_init_with_invalid_bucket(self):
        """Test initialization with invalid bucket."""
        with pytest.raises(S3UploadError):
            S3Uploader(bucket_name="non-existent-bucket")

    def test_generate_partition_path(self):
        """Test partition path generation."""
        with patch.object(S3Uploader, "__init__", lambda x, **kwargs: None):
            uploader = S3Uploader.__new__(S3Uploader)

            path = uploader._generate_partition_path(
                "games", date(2024, 1, 15), hour=10
            )

            expected = "nba-api/games/year=2024/month=01/day=15/hour=10/"
            assert path == expected

    def test_generate_partition_path_default_hour(self):
        """Test partition path generation with default hour."""
        with patch.object(S3Uploader, "__init__", lambda x, **kwargs: None):
            uploader = S3Uploader.__new__(S3Uploader)

            with patch("hoopstat_s3.s3_uploader.datetime") as mock_datetime:
                mock_datetime.now.return_value.hour = 14

                path = uploader._generate_partition_path("players", date(2024, 3, 1))

                expected = "nba-api/players/year=2024/month=03/day=01/hour=14/"
                assert path == expected

    @mock_aws
    def test_upload_to_s3(self):
        """Test S3 upload functionality."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        test_data = b"test parquet data"
        s3_key = "test/path/file.parquet"
        metadata = {"data_type": "test"}

        uploader._upload_to_s3(test_data, s3_key, metadata)

        # Verify upload
        response = conn.get_object(Bucket="test-bucket", Key=s3_key)
        assert response["Body"].read() == test_data
        assert response["Metadata"]["data_type"] == "test"

    @mock_aws
    def test_upload_games(self):
        """Test games data upload."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        test_data = b"games parquet data"
        target_date = date(2024, 1, 15)

        s3_key = uploader.upload_games(test_data, target_date)

        assert s3_key.startswith("nba-api/games/year=2024/month=01/day=15/hour=")
        assert s3_key.endswith(".parquet")

        # Verify data was uploaded
        response = conn.get_object(Bucket="test-bucket", Key=s3_key)
        assert response["Body"].read() == test_data
        assert response["Metadata"]["data_type"] == "games"

    @mock_aws
    def test_upload_games_empty_data(self):
        """Test games upload with empty data."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        s3_key = uploader.upload_games(b"", date(2024, 1, 15))
        assert s3_key == ""

    @mock_aws
    def test_upload_box_score(self):
        """Test box score data upload."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        test_data = b"box score parquet data"
        game_id = "0022300001"
        target_date = date(2024, 1, 15)

        s3_key = uploader.upload_box_score(test_data, game_id, target_date)

        assert s3_key.startswith("nba-api/box/year=2024/month=01/day=15/hour=")
        assert game_id in s3_key
        assert s3_key.endswith(".parquet")

        # Verify metadata
        response = conn.get_object(Bucket="test-bucket", Key=s3_key)
        assert response["Metadata"]["data_type"] == "box"
        assert response["Metadata"]["game_id"] == game_id

    @mock_aws
    def test_upload_player_info(self):
        """Test player info upload."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        test_data = b"player info parquet data"
        player_id = 12345

        s3_key = uploader.upload_player_info(test_data, player_id)

        assert "nba-api/players/" in s3_key
        assert str(player_id) in s3_key
        assert s3_key.endswith(".parquet")

        # Verify metadata
        response = conn.get_object(Bucket="test-bucket", Key=s3_key)
        assert response["Metadata"]["data_type"] == "players"
        assert response["Metadata"]["player_id"] == str(player_id)

    @mock_aws
    def test_upload_standings(self):
        """Test standings upload."""
        # Create mock bucket
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        uploader = S3Uploader(bucket_name="test-bucket")

        test_data = b"standings parquet data"

        s3_key = uploader.upload_standings(test_data)

        assert "nba-api/standings/" in s3_key
        assert s3_key.endswith(".parquet")

        # Verify metadata
        response = conn.get_object(Bucket="test-bucket", Key=s3_key)
        assert response["Metadata"]["data_type"] == "standings"

    @mock_aws
    def test_list_objects(self):
        """Test listing S3 objects."""
        # Create mock bucket and objects
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        # Upload test objects
        test_keys = [
            "nba-api/games/year=2024/month=01/day=15/hour=10/game1.parquet",
            "nba-api/games/year=2024/month=01/day=15/hour=10/game2.parquet",
            "nba-api/players/year=2024/month=01/day=15/hour=10/player1.parquet",
        ]

        for key in test_keys:
            conn.put_object(Bucket="test-bucket", Key=key, Body=b"test data")

        uploader = S3Uploader(bucket_name="test-bucket")

        # List games objects
        objects = uploader.list_objects("nba-api/games/")

        assert len(objects) == 2
        assert all("game" in obj["Key"] for obj in objects)

    def test_upload_error_handling(self):
        """Test error handling during upload."""
        with patch.object(S3Uploader, "__init__", lambda x, **kwargs: None):
            uploader = S3Uploader.__new__(S3Uploader)
            uploader.bucket_name = "test-bucket"

            # Mock S3 client that raises an error
            mock_client = Mock()
            mock_client.put_object.side_effect = Exception("Upload failed")
            uploader.s3_client = mock_client

            with pytest.raises(S3UploadError, match="S3 upload failed"):
                uploader._upload_to_s3(b"test data", "test/key", {})
