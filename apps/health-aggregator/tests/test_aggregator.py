"""
Tests for the core aggregation logic.

Validates daily summary construction, status derivation, sanitization,
and the full aggregate() happy path and degraded fallback.
"""

import datetime as dt
from unittest.mock import MagicMock

import pytest
from hoopstat_data.health_models import (
    OverallSystemStatus,
    PipelineHealthReport,
    PipelineStageStatus,
    StageStatus,
)

from app.aggregator import (
    HealthAggregator,
    _build_daily_summary,
    _build_stage_index,
    _derive_overall_status,
    _derive_stage_statuses,
    _map_stage_status,
    _parse_date,
    _safe_int,
    sanitize_report,
)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_cw_rows(
    date_str: str = "2024-01-15 00:00:00.000",
) -> list[dict[str, str]]:
    """Return a full set of three-stage CloudWatch rows for the given date."""
    return [
        {
            "execution_date": date_str,
            "stage": "bronze",
            "status": "success",
            "records_ingested": "100",
            "records_processed": "0",
            "records_quarantined": "0",
            "artifacts_written": "0",
        },
        {
            "execution_date": date_str,
            "stage": "silver",
            "status": "success",
            "records_ingested": "0",
            "records_processed": "95",
            "records_quarantined": "5",
            "artifacts_written": "0",
        },
        {
            "execution_date": date_str,
            "stage": "gold",
            "status": "success",
            "records_ingested": "0",
            "records_processed": "0",
            "records_quarantined": "0",
            "artifacts_written": "10",
        },
    ]


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_iso_date(self):
        assert _parse_date("2024-01-15") == dt.date(2024, 1, 15)

    def test_cloudwatch_timestamp(self):
        assert _parse_date("2024-01-15 00:00:00.000") == dt.date(2024, 1, 15)

    def test_iso_datetime(self):
        assert _parse_date("2024-03-28T12:00:00") == dt.date(2024, 3, 28)

    def test_invalid_returns_none(self):
        assert _parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# _safe_int
# ---------------------------------------------------------------------------


class TestSafeInt:
    def test_string_int(self):
        assert _safe_int("42") == 42

    def test_float_string(self):
        assert _safe_int("3.9") == 3

    def test_none_returns_default(self):
        assert _safe_int(None) == 0

    def test_invalid_returns_default(self):
        assert _safe_int("abc") == 0

    def test_custom_default(self):
        assert _safe_int(None, default=99) == 99


# ---------------------------------------------------------------------------
# _map_stage_status
# ---------------------------------------------------------------------------


class TestMapStageStatus:
    def test_success(self):
        assert _map_stage_status("success") == PipelineStageStatus.SUCCESS

    def test_failed(self):
        assert _map_stage_status("failed") == PipelineStageStatus.FAILED

    def test_skipped(self):
        assert _map_stage_status("skipped") == PipelineStageStatus.SKIPPED

    def test_unknown_returns_no_data(self):
        assert _map_stage_status("unknown_value") == PipelineStageStatus.NO_DATA

    def test_case_insensitive(self):
        assert _map_stage_status("SUCCESS") == PipelineStageStatus.SUCCESS


# ---------------------------------------------------------------------------
# _build_stage_index
# ---------------------------------------------------------------------------


class TestBuildStageIndex:
    def test_indexes_by_date_and_stage(self):
        rows = _make_cw_rows("2024-01-15 00:00:00.000")
        index = _build_stage_index(rows)
        date_key = dt.date(2024, 1, 15)
        assert date_key in index
        assert "bronze" in index[date_key]
        assert index[date_key]["bronze"]["status"] == "success"

    def test_skips_rows_with_missing_date(self):
        rows = [{"stage": "bronze", "status": "success"}]
        index = _build_stage_index(rows)
        assert index == {}

    def test_skips_rows_with_missing_stage(self):
        rows = [{"execution_date": "2024-01-15 00:00:00.000", "status": "success"}]
        index = _build_stage_index(rows)
        assert index == {}

    def test_multiple_dates(self):
        rows = _make_cw_rows("2024-01-15 00:00:00.000")
        rows += _make_cw_rows("2024-01-14 00:00:00.000")
        index = _build_stage_index(rows)
        assert len(index) == 2


# ---------------------------------------------------------------------------
# _build_daily_summary
# ---------------------------------------------------------------------------


class TestBuildDailySummary:
    def test_happy_path(self):
        rows = _make_cw_rows("2024-01-15 00:00:00.000")
        index = _build_stage_index(rows)
        summary = _build_daily_summary(dt.date(2024, 1, 15), index, quarantine_count=3)

        assert summary.date == dt.date(2024, 1, 15)
        assert summary.bronze.status == PipelineStageStatus.SUCCESS
        assert summary.bronze.records_ingested == 100
        assert summary.silver.records_quarantined == 3  # S3 count takes precedence
        assert summary.gold.artifacts_written == 10

    def test_missing_stage_data_defaults(self):
        """Missing CW data produces NO_DATA status and zero counts."""
        summary = _build_daily_summary(dt.date(2024, 1, 15), {}, quarantine_count=0)
        assert summary.bronze.status == PipelineStageStatus.NO_DATA
        assert summary.bronze.records_ingested == 0

    def test_quality_score_computed_from_counts(self):
        rows = _make_cw_rows("2024-01-15 00:00:00.000")
        index = _build_stage_index(rows)
        # 95 processed, 5 quarantined → quality = 95/100 = 0.95
        summary = _build_daily_summary(dt.date(2024, 1, 15), index, quarantine_count=5)
        assert summary.silver.quality_score == pytest.approx(0.95, abs=0.001)

    def test_quality_score_perfect_when_no_quarantine(self):
        rows = _make_cw_rows("2024-01-15 00:00:00.000")
        index = _build_stage_index(rows)
        summary = _build_daily_summary(dt.date(2024, 1, 15), index, quarantine_count=0)
        # 95 processed, 0 quarantined → quality = 1.0
        assert summary.silver.quality_score == pytest.approx(1.0, abs=0.001)

    def test_quality_score_zero_when_no_data_and_failed(self):
        rows = [
            {
                "execution_date": "2024-01-15 00:00:00.000",
                "stage": "silver",
                "status": "failed",
                "records_processed": "0",
                "records_quarantined": "0",
            }
        ]
        index = _build_stage_index(rows)
        summary = _build_daily_summary(dt.date(2024, 1, 15), index, quarantine_count=0)
        assert summary.silver.quality_score == 0.0


# ---------------------------------------------------------------------------
# _derive_stage_statuses
# ---------------------------------------------------------------------------


class TestDeriveStageStatuses:
    def _make_summaries(self, n=7, status="success"):
        """Create n daily summaries all with the same stage status."""
        from hoopstat_data.health_models import (
            BronzeDailySummary,
            DailySummary,
            GoldDailySummary,
            SilverDailySummary,
        )

        today = dt.date(2024, 1, 20)
        summaries = []
        for i in range(n):
            d = today - dt.timedelta(days=i)
            ps = (
                PipelineStageStatus(status)
                if status in PipelineStageStatus._value2member_map_
                else PipelineStageStatus.NO_DATA
            )
            summaries.append(
                DailySummary(
                    date=d,
                    bronze=BronzeDailySummary(status=ps, records_ingested=0),
                    silver=SilverDailySummary(
                        status=ps,
                        records_processed=0,
                        records_quarantined=0,
                        quality_score=1.0,
                    ),
                    gold=GoldDailySummary(status=ps, artifacts_written=0),
                )
            )
        return summaries

    def test_all_success_is_operational(self):
        summaries = self._make_summaries(status="success")
        statuses = _derive_stage_statuses(summaries, gold_last_success_at=None)
        for stage in ("bronze", "silver", "gold"):
            assert statuses[stage].status == OverallSystemStatus.OPERATIONAL

    def test_most_recent_failed_is_degraded(self):
        from hoopstat_data.health_models import (
            BronzeDailySummary,
            DailySummary,
            GoldDailySummary,
            SilverDailySummary,
        )

        summaries = self._make_summaries(status="success")
        # Overwrite the most recent day with failed status
        d = summaries[0].date
        summaries[0] = DailySummary(
            date=d,
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.FAILED, records_ingested=0
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.FAILED,
                records_processed=0,
                records_quarantined=0,
                quality_score=0.0,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.FAILED, artifacts_written=0
            ),
        )
        statuses = _derive_stage_statuses(summaries, gold_last_success_at=None)
        assert statuses["bronze"].status == OverallSystemStatus.DEGRADED

    def test_all_no_data_is_outage(self):
        summaries = self._make_summaries(status="no_data")
        statuses = _derive_stage_statuses(summaries, gold_last_success_at=None)
        assert statuses["bronze"].status == OverallSystemStatus.OUTAGE

    def test_gold_last_success_at_propagated(self):
        summaries = self._make_summaries(status="success")
        gold_ts = dt.datetime(2024, 1, 20, 12, 0, 0, tzinfo=dt.UTC)
        statuses = _derive_stage_statuses(summaries, gold_last_success_at=gold_ts)
        assert statuses["gold"].last_success_at == gold_ts


# ---------------------------------------------------------------------------
# _derive_overall_status
# ---------------------------------------------------------------------------


class TestDeriveOverallStatus:
    def _stages(self, **kwargs):
        return {
            k: StageStatus(status=v, last_success_at=None) for k, v in kwargs.items()
        }

    def test_all_operational(self):
        stages = self._stages(
            bronze=OverallSystemStatus.OPERATIONAL,
            silver=OverallSystemStatus.OPERATIONAL,
            gold=OverallSystemStatus.OPERATIONAL,
        )
        assert _derive_overall_status(stages) == OverallSystemStatus.OPERATIONAL

    def test_one_degraded(self):
        stages = self._stages(
            bronze=OverallSystemStatus.OPERATIONAL,
            silver=OverallSystemStatus.DEGRADED,
            gold=OverallSystemStatus.OPERATIONAL,
        )
        assert _derive_overall_status(stages) == OverallSystemStatus.DEGRADED

    def test_one_outage(self):
        stages = self._stages(
            bronze=OverallSystemStatus.OUTAGE,
            silver=OverallSystemStatus.OPERATIONAL,
            gold=OverallSystemStatus.OPERATIONAL,
        )
        assert _derive_overall_status(stages) == OverallSystemStatus.OUTAGE

    def test_outage_beats_degraded(self):
        stages = self._stages(
            bronze=OverallSystemStatus.OUTAGE,
            silver=OverallSystemStatus.DEGRADED,
            gold=OverallSystemStatus.OPERATIONAL,
        )
        assert _derive_overall_status(stages) == OverallSystemStatus.OUTAGE


# ---------------------------------------------------------------------------
# sanitize_report
# ---------------------------------------------------------------------------


class TestSanitizeReport:
    def test_clean_report_passes(self):
        report = {
            "overall_status": "operational",
            "generated_at": "2024-01-15T00:00:00Z",
        }
        result = sanitize_report(report)
        assert result is report  # same object returned

    def test_aws_arn_raises(self):
        report = {"message": "arn:aws:iam::123456789012:role/MyRole caused an error"}
        with pytest.raises(ValueError, match="Sensitive pattern"):
            sanitize_report(report)

    def test_aws_access_key_raises(self):
        report = {"key": "AKIAIOSFODNN7EXAMPLE"}
        with pytest.raises(ValueError, match="Sensitive pattern"):
            sanitize_report(report)

    def test_nested_sensitive_data_raises(self):
        report = {
            "stages": {"bronze": {"message": "AKIAIOSFODNN7EXAMPLE in nested field"}}
        }
        with pytest.raises(ValueError, match="Sensitive pattern"):
            sanitize_report(report)

    def test_list_sensitive_data_raises(self):
        report = {"errors": ["AKIAIOSFODNN7EXAMPLE"]}
        with pytest.raises(ValueError, match="Sensitive pattern"):
            sanitize_report(report)


# ---------------------------------------------------------------------------
# HealthAggregator.aggregate
# ---------------------------------------------------------------------------


class TestHealthAggregator:
    def _make_aggregator(self, cw_rows=None, quarantine_count=0, gold_ts=None):
        if cw_rows is None:
            today = dt.date.today()
            date_str = today.strftime("%Y-%m-%d") + " 00:00:00.000"
            cw_rows = _make_cw_rows(date_str)

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.return_value = cw_rows

        s3_mock = MagicMock()
        s3_mock.count_quarantine_files.return_value = quarantine_count
        s3_mock.get_gold_index_last_modified.return_value = gold_ts

        return HealthAggregator(
            cw_client=cw_mock,
            s3_reader=s3_mock,
            lookback_days=7,
        )

    def test_aggregate_returns_valid_report(self):
        aggregator = self._make_aggregator()
        report = aggregator.aggregate()

        assert isinstance(report, PipelineHealthReport)
        assert len(report.daily_summaries) == 7
        assert report.overall_status in OverallSystemStatus

    def test_aggregate_summaries_most_recent_first(self):
        aggregator = self._make_aggregator()
        report = aggregator.aggregate()

        dates = [s.date for s in report.daily_summaries]
        assert dates == sorted(dates, reverse=True)

    def test_aggregate_with_gold_timestamp(self):
        gold_ts = dt.datetime(2024, 1, 15, 12, 0, 0, tzinfo=dt.UTC)
        aggregator = self._make_aggregator(gold_ts=gold_ts)
        report = aggregator.aggregate()
        assert report.stages["gold"].last_success_at == gold_ts

    def test_aggregate_cw_failure_produces_degraded_report(self):
        """CloudWatch query failure results in a degraded (OUTAGE) report."""
        from app.cloudwatch import CloudWatchQueryError

        cw_mock = MagicMock()
        cw_mock.query_pipeline_status.side_effect = CloudWatchQueryError("Query failed")

        s3_mock = MagicMock()
        s3_mock.count_quarantine_files.return_value = 0
        s3_mock.get_gold_index_last_modified.return_value = None

        aggregator = HealthAggregator(
            cw_client=cw_mock, s3_reader=s3_mock, lookback_days=7
        )
        report = aggregator.aggregate()

        assert report.overall_status == OverallSystemStatus.OUTAGE
        assert len(report.daily_summaries) == 7
        for summary in report.daily_summaries:
            assert summary.bronze.status == PipelineStageStatus.NO_DATA

    def test_aggregate_no_cw_data_produces_no_data_report(self):
        """Empty CW results result in NO_DATA stages (not a crash)."""
        aggregator = self._make_aggregator(cw_rows=[])
        report = aggregator.aggregate()
        assert isinstance(report, PipelineHealthReport)
        # No data means OUTAGE at top level
        assert report.overall_status == OverallSystemStatus.OUTAGE

    def test_aggregate_quarantine_counts_used(self):
        aggregator = self._make_aggregator(quarantine_count=7)
        report = aggregator.aggregate()
        # Most recent day should have 7 quarantined records
        assert report.daily_summaries[0].silver.records_quarantined == 7
