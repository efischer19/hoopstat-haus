"""
Tests for the S3 reader utilities.

Uses moto to mock the S3 API so no real AWS calls are made.
"""

import datetime as dt

import boto3
import pytest
from moto import mock_aws

from app.s3_reader import S3Reader


@pytest.fixture
def aws_credentials(monkeypatch):
    """Ensure moto intercepts all boto3 calls by setting fake credentials."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def s3_buckets(aws_credentials):
    """Create mocked Bronze and Gold S3 buckets."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bronze")
        s3.create_bucket(Bucket="test-gold")
        yield s3


@pytest.fixture
def reader(s3_buckets):
    """S3Reader backed by the mocked S3."""
    return S3Reader(
        bronze_bucket="test-bronze",
        gold_bucket="test-gold",
        aws_region="us-east-1",
        s3_client=s3_buckets,
    )


class TestCountQuarantineFiles:
    """Tests for S3Reader.count_quarantine_files."""

    def test_no_quarantine_files_returns_zero(self, reader):
        """Returns 0 when the quarantine prefix has no objects."""
        count = reader.count_quarantine_files(dt.date(2024, 1, 15))
        assert count == 0

    def test_counts_files_correctly(self, s3_buckets, reader):
        """Returns the correct count of objects under the quarantine prefix."""
        prefix = "quarantine/year=2024/month=01/day=15/"
        for i in range(3):
            s3_buckets.put_object(
                Bucket="test-bronze",
                Key=f"{prefix}file_{i}.json",
                Body=b"{}",
            )

        count = reader.count_quarantine_files(dt.date(2024, 1, 15))
        assert count == 3

    def test_different_days_are_isolated(self, s3_buckets, reader):
        """Files from another day do not appear in today's count."""
        s3_buckets.put_object(
            Bucket="test-bronze",
            Key="quarantine/year=2024/month=01/day=14/old.json",
            Body=b"{}",
        )
        count = reader.count_quarantine_files(dt.date(2024, 1, 15))
        assert count == 0

    def test_zero_padded_month_and_day(self, s3_buckets, reader):
        """Month and day are zero-padded in the S3 prefix."""
        s3_buckets.put_object(
            Bucket="test-bronze",
            Key="quarantine/year=2024/month=03/day=05/q.json",
            Body=b"{}",
        )
        count = reader.count_quarantine_files(dt.date(2024, 3, 5))
        assert count == 1

    def test_client_error_returns_zero(self):
        """Returns 0 gracefully when S3 raises an error."""
        from unittest.mock import MagicMock

        from botocore.exceptions import ClientError

        s3_mock = MagicMock()
        paginator_mock = MagicMock()
        paginator_mock.paginate.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "ListObjectsV2",
        )
        s3_mock.get_paginator.return_value = paginator_mock

        reader = S3Reader(
            bronze_bucket="missing-bucket",
            gold_bucket="test-gold",
            aws_region="us-east-1",
            s3_client=s3_mock,
        )
        count = reader.count_quarantine_files(dt.date(2024, 1, 15))
        assert count == 0


class TestGetGoldIndexLastModified:
    """Tests for S3Reader.get_gold_index_last_modified."""

    def test_returns_last_modified_when_object_exists(self, s3_buckets, reader):
        """Returns a UTC-aware datetime when the Gold index exists."""
        s3_buckets.put_object(
            Bucket="test-gold",
            Key="served/index/latest.json",
            Body=b'{"latest_date": "2024-01-15"}',
        )

        result = reader.get_gold_index_last_modified()
        assert result is not None
        assert result.tzinfo is not None  # must be timezone-aware

    def test_returns_none_when_object_missing(self, reader):
        """Returns None when the Gold index does not exist."""
        result = reader.get_gold_index_last_modified()
        assert result is None

    def test_returns_none_on_client_error(self):
        """Returns None gracefully when head_object raises an unexpected error."""
        from unittest.mock import MagicMock

        from botocore.exceptions import ClientError

        s3_mock = MagicMock()
        s3_mock.head_object.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}},
            "HeadObject",
        )

        reader = S3Reader(
            bronze_bucket="test-bronze",
            gold_bucket="test-gold",
            aws_region="us-east-1",
            s3_client=s3_mock,
        )
        result = reader.get_gold_index_last_modified()
        assert result is None
