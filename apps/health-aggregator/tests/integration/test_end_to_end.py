"""
End-to-end integration tests for the health dashboard pipeline.

Validates the complete aggregation pipeline using moto-mocked AWS services
(CloudWatch Logs, S3) per the 5 scenarios defined in the integration testing
issue.  Each scenario exercises the real HealthAggregator, S3Reader,
HealthReportWriter, and sanitizer code — only the AWS backends are mocked.

Scenarios
---------
1. Happy path — all pipelines operational
2. Pipeline failure — Bronze fails
3. Degraded state — Silver quarantines
4. Security — injected secrets rejected by sanitizer
5. Resilience — CloudWatch unavailable (timeout/error)
"""

import datetime as dt
import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from hoopstat_data.health_models import (
    OverallSystemStatus,
    PipelineHealthReport,
    PipelineStageStatus,
)
from moto import mock_aws

from app.aggregator import HealthAggregator
from app.cloudwatch import CloudWatchQueryError
from app.s3_reader import S3Reader
from app.sanitizer import sanitize_report
from app.writer import HEALTH_ARTIFACT_KEY, HealthReportWriter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRONZE_BUCKET = "test-bronze-bucket"
GOLD_BUCKET = "test-gold-bucket"
AWS_REGION = "us-east-1"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def s3_client():
    """Create a moto-mocked S3 client with Bronze and Gold buckets."""
    with mock_aws():
        client = boto3.client("s3", region_name=AWS_REGION)
        client.create_bucket(Bucket=BRONZE_BUCKET)
        client.create_bucket(Bucket=GOLD_BUCKET)
        yield client


def _today_str():
    """Return today's date as 'YYYY-MM-DD 00:00:00.000' for CW mock rows."""
    return dt.date.today().strftime("%Y-%m-%d") + " 00:00:00.000"


def _date_str(offset_days: int = 0) -> str:
    """Return a date string N days ago in CloudWatch format."""
    d = dt.date.today() - dt.timedelta(days=offset_days)
    return d.strftime("%Y-%m-%d") + " 00:00:00.000"


def _make_cw_rows_for_day(
    date_str: str,
    bronze_status: str = "success",
    silver_status: str = "success",
    gold_status: str = "success",
    records_ingested: str = "100",
    records_processed: str = "95",
    records_quarantined: str = "5",
    artifacts_written: str = "10",
) -> list[dict[str, str]]:
    """Build a full set of three-stage CloudWatch rows for one day."""
    return [
        {
            "execution_date": date_str,
            "stage": "bronze",
            "status": bronze_status,
            "records_ingested": records_ingested,
            "records_processed": "0",
            "records_quarantined": "0",
            "artifacts_written": "0",
        },
        {
            "execution_date": date_str,
            "stage": "silver",
            "status": silver_status,
            "records_ingested": "0",
            "records_processed": records_processed,
            "records_quarantined": records_quarantined,
            "artifacts_written": "0",
        },
        {
            "execution_date": date_str,
            "stage": "gold",
            "status": gold_status,
            "records_ingested": "0",
            "records_processed": "0",
            "records_quarantined": "0",
            "artifacts_written": artifacts_written,
        },
    ]


def _build_7day_cw_rows(
    overrides_by_offset: dict[int, dict] | None = None,
) -> list[dict[str, str]]:
    """
    Build 7 days of CloudWatch rows.

    By default all days are success.  Pass overrides like
    ``{0: {"bronze_status": "failed"}}`` to override specific days
    (offset 0 = today).
    """
    if overrides_by_offset is None:
        overrides_by_offset = {}
    rows: list[dict[str, str]] = []
    for offset in range(7):
        day_kwargs = overrides_by_offset.get(offset, {})
        rows.extend(_make_cw_rows_for_day(_date_str(offset), **day_kwargs))
    return rows


def _put_quarantine_files(s3_client, target_date: dt.date, count: int) -> None:
    """Create *count* quarantine objects in the Bronze bucket for *target_date*."""
    prefix = (
        f"quarantine/year={target_date.year}/"
        f"month={target_date.month:02d}/"
        f"day={target_date.day:02d}/"
    )
    for i in range(count):
        s3_client.put_object(
            Bucket=BRONZE_BUCKET,
            Key=f"{prefix}record_{i}.json",
            Body=b"{}",
        )


def _put_gold_index(s3_client) -> None:
    """Create a Gold latest.json artifact in the Gold bucket."""
    s3_client.put_object(
        Bucket=GOLD_BUCKET,
        Key="served/index/latest.json",
        Body=json.dumps({"latest_date": str(dt.date.today())}).encode(),
        ContentType="application/json",
    )


def _read_health_artifact(s3_client) -> dict:
    """Read and parse the written pipeline_health.json from the Gold bucket."""
    obj = s3_client.get_object(Bucket=GOLD_BUCKET, Key=HEALTH_ARTIFACT_KEY)
    return json.loads(obj["Body"].read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Scenario 1: Happy Path — All Pipelines Operational
# ---------------------------------------------------------------------------


class TestScenario1HappyPath:
    """All three pipeline stages succeed for all 7 days."""

    def test_happy_path_overall_status_is_operational(self, s3_client):
        """Pipeline with all stages succeeding should report operational."""
        cw_rows = _build_7day_cw_rows()

        # Put quarantine files for today (small count — pipeline is healthy)
        _put_quarantine_files(s3_client, dt.date.today(), count=2)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        assert isinstance(report, PipelineHealthReport)
        assert report.overall_status == OverallSystemStatus.OPERATIONAL
        assert len(report.daily_summaries) == 7
        assert report.schema_version == "1.0.0"

    def test_happy_path_record_counts_correct(self, s3_client):
        """Record counts from CloudWatch and S3 appear in the report."""
        cw_rows = _build_7day_cw_rows()
        _put_quarantine_files(s3_client, dt.date.today(), count=3)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        today_summary = report.daily_summaries[0]
        assert today_summary.bronze.records_ingested == 100
        assert today_summary.silver.records_processed == 95
        # S3 quarantine count takes precedence over CW field
        assert today_summary.silver.records_quarantined == 3
        assert today_summary.gold.artifacts_written == 10

    def test_happy_path_write_to_s3_produces_valid_json(self, s3_client):
        """The full pipeline writes valid JSON to S3 with correct schema."""
        cw_rows = _build_7day_cw_rows()
        _put_quarantine_files(s3_client, dt.date.today(), count=0)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )
        writer = HealthReportWriter(gold_bucket=GOLD_BUCKET, s3_client=s3_client)

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()
        writer.write(report)

        artifact = _read_health_artifact(s3_client)
        assert artifact["overall_status"] == "operational"
        assert artifact["schema_version"] == "1.0.0"
        assert len(artifact["daily_summaries"]) == 7

    def test_happy_path_all_stages_operational(self, s3_client):
        """Each stage (bronze, silver, gold) should be operational."""
        cw_rows = _build_7day_cw_rows()
        _put_quarantine_files(s3_client, dt.date.today(), count=0)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        for stage_name in ("bronze", "silver", "gold"):
            assert stage_name in report.stages
            assert (
                report.stages[stage_name].status == OverallSystemStatus.OPERATIONAL
            ), f"Expected {stage_name} to be operational"


# ---------------------------------------------------------------------------
# Scenario 2: Pipeline Failure — Bronze Fails
# ---------------------------------------------------------------------------


class TestScenario2BronzeFailure:
    """Bronze ingestion fails; Silver and Gold have no data."""

    def test_bronze_failure_overall_status_is_outage(self, s3_client):
        """When Bronze fails and Silver/Gold have no data, overall is outage."""
        # Only provide Bronze rows (failed), no Silver/Gold data at all
        cw_rows = []
        for offset in range(7):
            date_str = _date_str(offset)
            cw_rows.append(
                {
                    "execution_date": date_str,
                    "stage": "bronze",
                    "status": "failed",
                    "records_ingested": "0",
                    "records_processed": "0",
                    "records_quarantined": "0",
                    "artifacts_written": "0",
                }
            )

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        assert report.overall_status == OverallSystemStatus.OUTAGE

    def test_bronze_failure_bronze_stage_is_degraded(self, s3_client):
        """Bronze stage status is DEGRADED when most recent run failed."""
        cw_rows = []
        for offset in range(7):
            date_str = _date_str(offset)
            cw_rows.append(
                {
                    "execution_date": date_str,
                    "stage": "bronze",
                    "status": "failed",
                    "records_ingested": "0",
                    "records_processed": "0",
                    "records_quarantined": "0",
                    "artifacts_written": "0",
                }
            )

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        # Bronze most recent is failed → DEGRADED
        assert report.stages["bronze"].status == OverallSystemStatus.DEGRADED

    def test_bronze_failure_silver_gold_are_no_data(self, s3_client):
        """Silver and Gold stages show OUTAGE when no data exists."""
        cw_rows = []
        for offset in range(7):
            date_str = _date_str(offset)
            cw_rows.append(
                {
                    "execution_date": date_str,
                    "stage": "bronze",
                    "status": "failed",
                    "records_ingested": "0",
                    "records_processed": "0",
                    "records_quarantined": "0",
                    "artifacts_written": "0",
                }
            )

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        # Silver and Gold have no CW rows → NO_DATA → OUTAGE
        assert report.stages["silver"].status == OverallSystemStatus.OUTAGE
        assert report.stages["gold"].status == OverallSystemStatus.OUTAGE

    def test_bronze_failure_written_artifact_reflects_outage(self, s3_client):
        """Written JSON artifact reflects the outage state correctly."""
        cw_rows = []
        for offset in range(7):
            date_str = _date_str(offset)
            cw_rows.append(
                {
                    "execution_date": date_str,
                    "stage": "bronze",
                    "status": "failed",
                    "records_ingested": "0",
                    "records_processed": "0",
                    "records_quarantined": "0",
                    "artifacts_written": "0",
                }
            )

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )
        writer = HealthReportWriter(gold_bucket=GOLD_BUCKET, s3_client=s3_client)

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()
        writer.write(report)

        artifact = _read_health_artifact(s3_client)
        assert artifact["overall_status"] == "outage"


# ---------------------------------------------------------------------------
# Scenario 3: Degraded State — Silver Quarantines
# ---------------------------------------------------------------------------


class TestScenario3SilverQuarantine:
    """Silver processing quarantines a significant number of records."""

    def test_high_quarantine_count_reports_correct_counts(self, s3_client):
        """High quarantine counts are reported accurately.

        Quarantine volume does not affect overall status — all stages
        succeeded, so overall remains OPERATIONAL.
        """
        # Most recent day: Silver has many quarantined records
        overrides = {
            0: {
                "silver_status": "success",
                "records_processed": "50",
                "records_quarantined": "50",
            }
        }
        cw_rows = _build_7day_cw_rows(overrides)

        # Put 50 quarantine files in S3 for today
        _put_quarantine_files(s3_client, dt.date.today(), count=50)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        # All stages succeeded → overall OPERATIONAL
        # (quarantine count reflects data quality, not stage failure)
        assert report.overall_status == OverallSystemStatus.OPERATIONAL
        assert report.daily_summaries[0].silver.records_quarantined == 50

    def test_quarantine_counts_accurate_across_days(self, s3_client):
        """Quarantine counts from S3 are accurately reflected per day."""
        cw_rows = _build_7day_cw_rows()

        # Different quarantine counts per day
        today = dt.date.today()
        _put_quarantine_files(s3_client, today, count=10)
        _put_quarantine_files(s3_client, today - dt.timedelta(days=1), count=5)
        _put_quarantine_files(s3_client, today - dt.timedelta(days=2), count=0)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        assert report.daily_summaries[0].silver.records_quarantined == 10
        assert report.daily_summaries[1].silver.records_quarantined == 5
        assert report.daily_summaries[2].silver.records_quarantined == 0

    def test_quality_score_reflects_quarantine_ratio(self, s3_client):
        """Quality score is computed from processed vs quarantined counts."""
        overrides = {
            0: {
                "silver_status": "success",
                "records_processed": "80",
                "records_quarantined": "20",
            }
        }
        cw_rows = _build_7day_cw_rows(overrides)
        _put_quarantine_files(s3_client, dt.date.today(), count=20)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        # quality_score = 80 / (80 + 20) = 0.8
        assert report.daily_summaries[0].silver.quality_score == pytest.approx(
            0.8, abs=0.01
        )

    def test_degraded_silver_written_artifact_shows_quarantine(self, s3_client):
        """Written JSON artifact includes accurate quarantine data."""
        overrides = {
            0: {
                "silver_status": "success",
                "records_processed": "70",
                "records_quarantined": "30",
            }
        }
        cw_rows = _build_7day_cw_rows(overrides)
        _put_quarantine_files(s3_client, dt.date.today(), count=30)
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )
        writer = HealthReportWriter(gold_bucket=GOLD_BUCKET, s3_client=s3_client)

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()
        writer.write(report)

        artifact = _read_health_artifact(s3_client)
        today_data = artifact["daily_summaries"][0]
        assert today_data["silver"]["records_quarantined"] == 30
        assert today_data["silver"]["records_processed"] == 70


# ---------------------------------------------------------------------------
# Scenario 4: Security — Injected Secrets
# ---------------------------------------------------------------------------


class TestScenario4SecurityInjectedSecrets:
    """Injected secret patterns are detected and rejected by the sanitizer."""

    def _make_report_with_injected_secret(
        self, secret_value: str
    ) -> PipelineHealthReport:
        """Create a report where a field has been tampered with a secret."""
        from hoopstat_data.health_models import (
            BronzeDailySummary,
            DailySummary,
            GoldDailySummary,
            SilverDailySummary,
            StageStatus,
        )

        # Cannot inject the secret into the generated_at field (datetime
        # type), so we test via the sanitizer's serialized JSON scanning
        # by creating a valid report first, then verifying that the
        # sanitizer catches secrets that might leak through an allowlist
        # bug.
        return PipelineHealthReport(
            generated_at=dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages={
                "bronze": StageStatus(
                    status=OverallSystemStatus.OPERATIONAL, last_success_at=None
                ),
                "silver": StageStatus(
                    status=OverallSystemStatus.OPERATIONAL, last_success_at=None
                ),
                "gold": StageStatus(
                    status=OverallSystemStatus.OPERATIONAL, last_success_at=None
                ),
            },
            daily_summaries=[
                DailySummary(
                    date=dt.date(2024, 1, 15),
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
            ],
        )

    def test_aws_access_key_triggers_fallback(self):
        """An AWS access key pattern in the serialized output triggers rejection."""
        report = self._make_report_with_injected_secret("AKIAIOSFODNN7EXAMPLE")

        # Patch the allowlist reconstruction to inject the secret
        with patch("app.sanitizer._reconstruct_allowlisted_dict") as mock_reconstruct:
            mock_reconstruct.return_value = {
                "schema_version": "1.0.0",
                "generated_at": "2024-01-15T00:00:00Z",
                "overall_status": "operational",
                "stages": {},
                "daily_summaries": [],
                "leaked_field": "AKIAIOSFODNN7EXAMPLE",
            }
            result = sanitize_report(report)

        assert result.overall_status == OverallSystemStatus.DEGRADED
        assert result.daily_summaries == []
        assert result.stages == {}

    def test_aws_arn_triggers_fallback(self):
        """An AWS ARN pattern in the serialized output triggers rejection."""
        report = self._make_report_with_injected_secret("")

        with patch("app.sanitizer._reconstruct_allowlisted_dict") as mock_reconstruct:
            mock_reconstruct.return_value = {
                "schema_version": "1.0.0",
                "generated_at": "2024-01-15T00:00:00Z",
                "overall_status": "operational",
                "stages": {},
                "daily_summaries": [],
                "leaked_arn": "arn:aws:lambda:us-east-1:123456789012:function:my-func",
            }
            result = sanitize_report(report)

        assert result.overall_status == OverallSystemStatus.DEGRADED

    def test_internal_ip_triggers_fallback(self):
        """An RFC 1918 internal IP triggers rejection."""
        report = self._make_report_with_injected_secret("")

        with patch("app.sanitizer._reconstruct_allowlisted_dict") as mock_reconstruct:
            mock_reconstruct.return_value = {
                "schema_version": "1.0.0",
                "generated_at": "2024-01-15T00:00:00Z",
                "overall_status": "operational",
                "stages": {},
                "daily_summaries": [],
                "leaked_ip": "10.0.1.42",
            }
            result = sanitize_report(report)

        assert result.overall_status == OverallSystemStatus.DEGRADED

    def test_bearer_token_triggers_fallback(self):
        """A Bearer token pattern in the serialized output triggers rejection."""
        report = self._make_report_with_injected_secret("")

        with patch("app.sanitizer._reconstruct_allowlisted_dict") as mock_reconstruct:
            mock_reconstruct.return_value = {
                "schema_version": "1.0.0",
                "generated_at": "2024-01-15T00:00:00Z",
                "overall_status": "operational",
                "stages": {},
                "daily_summaries": [],
                "auth": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            }
            result = sanitize_report(report)

        assert result.overall_status == OverallSystemStatus.DEGRADED

    def test_fallback_contains_no_secrets(self):
        """The fallback report produced on rejection contains no secret patterns."""
        from app.sanitizer import _contains_secrets

        report = self._make_report_with_injected_secret("")

        with patch("app.sanitizer._reconstruct_allowlisted_dict") as mock_reconstruct:
            mock_reconstruct.return_value = {
                "schema_version": "1.0.0",
                "generated_at": "2024-01-15T00:00:00Z",
                "overall_status": "operational",
                "stages": {},
                "daily_summaries": [],
                "secret_key": "AKIAIOSFODNN7EXAMPLE",
            }
            result = sanitize_report(report)

        # Verify the fallback JSON contains no secrets
        fallback_json = json.dumps(result.model_dump(mode="json"))
        assert not _contains_secrets(fallback_json)
        assert "AKIA" not in fallback_json
        assert "arn:aws" not in fallback_json

    def test_extra_cw_fields_stripped_by_allowlist(self, s3_client):
        """
        Full pipeline: extra fields in CW data are stripped by allowlist reconstruction.

        The allowlist in Pass 1 only maps known fields (execution_date, stage,
        status, etc.) into the Pydantic report.  Extra fields injected into the
        CloudWatch rows (like a leaked secret) are never propagated into the
        report because the aggregator only reads explicitly named fields.
        """
        # Inject an AWS key into a CloudWatch row's status field
        cw_rows = []
        for offset in range(7):
            date_str = _date_str(offset)
            cw_rows.extend(_make_cw_rows_for_day(date_str))

        # Tamper with a field that the allowlist should strip
        cw_rows[0]["leaked_secret"] = "AKIAIOSFODNN7EXAMPLE"

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        # The allowlist reconstruction should have stripped the extra field.
        # Verify the final report JSON contains no secret patterns.
        from app.sanitizer import _contains_secrets

        report_json = json.dumps(report.model_dump(mode="json"))
        assert not _contains_secrets(report_json)
        assert "AKIA" not in report_json

    def test_secret_in_written_artifact_never_persisted(self, s3_client):
        """Secrets injected into CW mock data never appear in the S3 artifact."""
        cw_rows = _build_7day_cw_rows()
        # Inject secrets into CW rows — these are extra fields the aggregator
        # does not map, so they should be stripped by the allowlist.
        cw_rows[0]["leaked_key"] = "AKIAIOSFODNN7EXAMPLE"
        cw_rows[1]["internal_ip"] = "10.0.1.42"
        cw_rows[2]["auth_header"] = "Bearer eyJhbGciOiJIUzI1NiJ9.test"
        _put_gold_index(s3_client)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )
        writer = HealthReportWriter(gold_bucket=GOLD_BUCKET, s3_client=s3_client)

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()
        writer.write(report)

        artifact = _read_health_artifact(s3_client)
        artifact_json = json.dumps(artifact)

        # Verify none of the injected secret patterns appear
        assert "AKIA" not in artifact_json
        assert "10.0.1.42" not in artifact_json
        assert "Bearer " not in artifact_json
        assert "secret_access_key" not in artifact_json.lower()


# ---------------------------------------------------------------------------
# Scenario 5: Resilience — CloudWatch Unavailable
# ---------------------------------------------------------------------------


class TestScenario5CloudWatchUnavailable:
    """CloudWatch Logs Insights query times out or fails."""

    def test_cw_timeout_produces_degraded_report(self, s3_client):
        """CloudWatch query timeout results in a degraded (OUTAGE) report."""
        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = CloudWatchQueryError(
            "CloudWatch query timed out after 60s"
        )

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        assert isinstance(report, PipelineHealthReport)
        assert report.overall_status == OverallSystemStatus.OUTAGE
        assert len(report.daily_summaries) == 7

    def test_cw_timeout_all_stages_no_data(self, s3_client):
        """All daily summaries have NO_DATA status when CloudWatch is down."""
        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = CloudWatchQueryError("Query failed")

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        for summary in report.daily_summaries:
            assert summary.bronze.status == PipelineStageStatus.NO_DATA
            assert summary.silver.status == PipelineStageStatus.NO_DATA
            assert summary.gold.status == PipelineStageStatus.NO_DATA

    def test_cw_timeout_stage_statuses_are_outage(self, s3_client):
        """All stage-level statuses show OUTAGE when CloudWatch is down."""
        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = CloudWatchQueryError(
            "Access denied"
        )

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        for stage_name in ("bronze", "silver", "gold"):
            assert report.stages[stage_name].status == OverallSystemStatus.OUTAGE

    def test_cw_timeout_writes_valid_artifact(self, s3_client):
        """Even when CloudWatch is down, a valid JSON artifact is written."""
        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = CloudWatchQueryError(
            "Network timeout"
        )

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )
        writer = HealthReportWriter(gold_bucket=GOLD_BUCKET, s3_client=s3_client)

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()
        writer.write(report)

        artifact = _read_health_artifact(s3_client)
        assert artifact["overall_status"] == "outage"
        assert artifact["schema_version"] == "1.0.0"
        assert len(artifact["daily_summaries"]) == 7

    def test_cw_generic_exception_produces_degraded_report(self, s3_client):
        """Any exception during CW query produces a degraded report."""
        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = Exception("Unexpected AWS error")

        s3_reader = S3Reader(
            bronze_bucket=BRONZE_BUCKET,
            gold_bucket=GOLD_BUCKET,
            s3_client=s3_client,
        )

        aggregator = HealthAggregator(cw_client=cw_mock, s3_reader=s3_reader)
        report = aggregator.aggregate()

        assert report.overall_status == OverallSystemStatus.OUTAGE
