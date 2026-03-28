"""
Tests for the HealthReportWriter.

Uses moto to mock S3 so no real AWS calls are made.
"""

import datetime as dt
import json

import boto3
import pytest
from hoopstat_data.health_models import (
    BronzeDailySummary,
    DailySummary,
    GoldDailySummary,
    OverallSystemStatus,
    PipelineHealthReport,
    PipelineStageStatus,
    SilverDailySummary,
    StageStatus,
)
from moto import mock_aws

from app.writer import CACHE_CONTROL, HEALTH_ARTIFACT_KEY, HealthReportWriter


@pytest.fixture
def aws_credentials(monkeypatch):
    """Ensure moto intercepts all boto3 calls."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mock_s3(aws_credentials):
    """Create a mocked Gold S3 bucket."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-gold")
        yield s3


@pytest.fixture
def writer(mock_s3):
    return HealthReportWriter(
        gold_bucket="test-gold",
        aws_region="us-east-1",
        s3_client=mock_s3,
    )


@pytest.fixture
def sample_report():
    """Minimal valid PipelineHealthReport for testing."""
    today = dt.date(2024, 1, 15)
    generated_at = dt.datetime(2024, 1, 15, 12, 0, 0, tzinfo=dt.UTC)

    daily_summaries = []
    for i in range(3):
        d = today - dt.timedelta(days=i)
        daily_summaries.append(
            DailySummary(
                date=d,
                bronze=BronzeDailySummary(
                    status=PipelineStageStatus.SUCCESS, records_ingested=100
                ),
                silver=SilverDailySummary(
                    status=PipelineStageStatus.SUCCESS,
                    records_processed=95,
                    records_quarantined=5,
                    quality_score=0.95,
                ),
                gold=GoldDailySummary(
                    status=PipelineStageStatus.SUCCESS, artifacts_written=10
                ),
            )
        )

    return PipelineHealthReport(
        generated_at=generated_at,
        overall_status=OverallSystemStatus.OPERATIONAL,
        stages={
            "bronze": StageStatus(
                status=OverallSystemStatus.OPERATIONAL,
                last_success_at=generated_at,
            ),
            "silver": StageStatus(
                status=OverallSystemStatus.OPERATIONAL,
                last_success_at=generated_at,
            ),
            "gold": StageStatus(
                status=OverallSystemStatus.OPERATIONAL,
                last_success_at=generated_at,
            ),
        },
        daily_summaries=daily_summaries,
    )


class TestHealthReportWriter:
    def test_write_creates_object_in_s3(self, writer, mock_s3, sample_report):
        """write() creates the expected S3 object."""
        writer.write(sample_report)

        response = mock_s3.get_object(Bucket="test-gold", Key=HEALTH_ARTIFACT_KEY)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_write_sets_cache_control(self, writer, mock_s3, sample_report):
        """write() sets Cache-Control: public, max-age=3600."""
        writer.write(sample_report)

        head = mock_s3.head_object(Bucket="test-gold", Key=HEALTH_ARTIFACT_KEY)
        assert head["CacheControl"] == CACHE_CONTROL

    def test_write_sets_content_type(self, writer, mock_s3, sample_report):
        """write() sets Content-Type to application/json."""
        writer.write(sample_report)

        head = mock_s3.head_object(Bucket="test-gold", Key=HEALTH_ARTIFACT_KEY)
        assert head["ContentType"] == "application/json"

    def test_write_produces_valid_json(self, writer, mock_s3, sample_report):
        """The uploaded body is valid JSON that can be round-tripped."""
        writer.write(sample_report)

        response = mock_s3.get_object(Bucket="test-gold", Key=HEALTH_ARTIFACT_KEY)
        body = response["Body"].read().decode("utf-8")
        data = json.loads(body)

        assert data["overall_status"] == "operational"
        assert "daily_summaries" in data
        assert len(data["daily_summaries"]) == 3

    def test_write_raises_runtime_error_on_s3_failure(self, sample_report):
        """write() raises RuntimeError when S3 put_object fails."""
        from unittest.mock import MagicMock

        from botocore.exceptions import ClientError

        s3_mock = MagicMock()
        s3_mock.put_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "PutObject",
        )

        writer = HealthReportWriter(
            gold_bucket="missing-bucket",
            aws_region="us-east-1",
            s3_client=s3_mock,
        )

        with pytest.raises(RuntimeError, match="Failed to write pipeline_health.json"):
            writer.write(sample_report)

    def test_written_json_contains_schema_version(self, writer, mock_s3, sample_report):
        """Serialised JSON includes the schema_version field."""
        writer.write(sample_report)

        response = mock_s3.get_object(Bucket="test-gold", Key=HEALTH_ARTIFACT_KEY)
        data = json.loads(response["Body"].read())
        assert "schema_version" in data
        assert data["schema_version"] == "1.0.0"
