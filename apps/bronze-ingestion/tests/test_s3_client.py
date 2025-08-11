"""Tests for the S3 Parquet client."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import BronzeIngestionConfig
from hoopstat_nba_ingestion import S3ParquetClient


class TestS3ParquetClient:
    """Test S3 Parquet client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=BronzeIngestionConfig)
        self.config.aws_region = "us-east-1"
        self.config.bronze_bucket_name = "test-bucket"

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_init_success(self, mock_boto3_client):
        """Test successful S3 client initialization."""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        mock_boto3_client.assert_called_once_with("s3", region_name="us-east-1")
        mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
        assert client.s3_client == mock_s3_client

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_init_no_credentials(self, mock_boto3_client):
        """Test initialization fails with no AWS credentials."""
        mock_boto3_client.side_effect = NoCredentialsError()

        with pytest.raises(ValueError, match="AWS credentials not found"):
            S3ParquetClient(self.config)

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_init_bucket_not_found(self, mock_boto3_client):
        """Test initialization fails when bucket doesn't exist."""
        mock_s3_client = Mock()
        mock_s3_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "head_bucket"
        )
        mock_boto3_client.return_value = mock_s3_client

        with pytest.raises(ValueError, match="S3 bucket not found"):
            S3ParquetClient(self.config)

    def test_build_s3_key(self):
        """Test S3 key building follows the correct pattern."""
        with patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client"):
            client = S3ParquetClient(self.config)

            key = client._build_s3_key("schedule", "2024-01-15")
            assert key == "raw/schedule/date=2024-01-15/data.parquet"

            key = client._build_s3_key("box_score", "2024-12-25")
            assert key == "raw/box_score/date=2024-12-25/data.parquet"

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_write_parquet_success(self, mock_boto3_client):
        """Test successful Parquet file writing to S3."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        # Test data
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        # Mock the entire Parquet process by patching the whole method behavior
        with patch.object(
            client,
            "_build_s3_key",
            return_value="raw/schedule/date=2024-01-15/data.parquet",
        ):
            with patch("hoopstat_nba_ingestion.s3_parquet_client.BytesIO") as mock_bytesio_class:
                with patch("hoopstat_nba_ingestion.s3_parquet_client.pa") as mock_pa:
                    with patch("hoopstat_nba_ingestion.s3_parquet_client.pq"):  # Don't need to assign
                        # Setup mocks
                        mock_buffer = Mock()
                        mock_buffer.getvalue.return_value = b"parquet_data"
                        mock_buffer.seek.return_value = None
                        mock_bytesio_class.return_value = mock_buffer

                        mock_table = Mock()
                        mock_pa.Table.from_pandas.return_value = mock_table

                        result = client.write_parquet(df, "schedule", "2024-01-15")

        # Verify S3 put_object was called correctly
        expected_key = "raw/schedule/date=2024-01-15/data.parquet"
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=expected_key,
            Body=b"parquet_data",
            ContentType="application/octet-stream",
        )

        # Verify return value
        assert result == f"s3://test-bucket/{expected_key}"

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_write_parquet_empty_dataframe(self, mock_boto3_client):
        """Test writing empty DataFrame is skipped."""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        # Test with empty DataFrame
        df = pd.DataFrame()
        result = client.write_parquet(df, "schedule", "2024-01-15")

        # Should not call S3 put_object
        mock_s3_client.put_object.assert_not_called()
        assert result == ""

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_write_parquet_no_overwrite_existing(self, mock_boto3_client):
        """Test writing with overwrite=False when file exists."""
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client

        # Mock that file exists
        mock_s3_client.head_object.return_value = {}

        client = S3ParquetClient(self.config)
        df = pd.DataFrame({"col1": [1, 2]})

        result = client.write_parquet(df, "schedule", "2024-01-15", overwrite=False)

        # Should check for file existence but not write
        expected_key = "raw/schedule/date=2024-01-15/data.parquet"
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key=expected_key
        )
        mock_s3_client.put_object.assert_not_called()
        assert result == f"s3://test-bucket/{expected_key}"

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_file_exists_true(self, mock_boto3_client):
        """Test file_exists returns True when file exists."""
        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {}
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        result = client.file_exists("schedule", "2024-01-15")

        assert result is True
        expected_key = "raw/schedule/date=2024-01-15/data.parquet"
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key=expected_key
        )

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_file_exists_false(self, mock_boto3_client):
        """Test file_exists returns False when file doesn't exist."""
        mock_s3_client = Mock()
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "head_object"
        )
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        result = client.file_exists("schedule", "2024-01-15")

        assert result is False

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    @patch("hoopstat_nba_ingestion.s3_parquet_client.pq.read_table")
    def test_read_parquet_success(self, mock_read_table, mock_boto3_client):
        """Test successful Parquet file reading from S3."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_response = {"Body": Mock(read=Mock(return_value=b"parquet_data"))}
        mock_s3_client.get_object.return_value = mock_response
        mock_boto3_client.return_value = mock_s3_client

        # Mock parquet reading
        mock_table = Mock()
        mock_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        mock_table.to_pandas.return_value = mock_df
        mock_read_table.return_value = mock_table

        client = S3ParquetClient(self.config)

        result = client.read_parquet("schedule", "2024-01-15")

        # Verify S3 get_object was called correctly
        expected_key = "raw/schedule/date=2024-01-15/data.parquet"
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key=expected_key
        )

        # Verify result
        pd.testing.assert_frame_equal(result, mock_df)

    @patch("hoopstat_nba_ingestion.s3_parquet_client.boto3.client")
    def test_read_parquet_file_not_found(self, mock_boto3_client):
        """Test reading non-existent file returns None."""
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "get_object"
        )
        mock_boto3_client.return_value = mock_s3_client

        client = S3ParquetClient(self.config)

        result = client.read_parquet("schedule", "2024-01-15")

        assert result is None
