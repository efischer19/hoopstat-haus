"""
Tests for pipeline health data models.
"""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

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

# ── Enum Tests ──────────────────────────────────────────────────────


class TestPipelineStageStatus:
    """Test PipelineStageStatus enum values."""

    def test_valid_values(self):
        """Test all valid pipeline stage status values."""
        assert PipelineStageStatus.SUCCESS == "success"
        assert PipelineStageStatus.FAILED == "failed"
        assert PipelineStageStatus.SKIPPED == "skipped"
        assert PipelineStageStatus.NO_DATA == "no_data"

    def test_string_conversion(self):
        """Test that enum values behave as strings."""
        assert str(PipelineStageStatus.SUCCESS) == "success"
        assert PipelineStageStatus("failed") == PipelineStageStatus.FAILED


class TestOverallSystemStatus:
    """Test OverallSystemStatus enum values."""

    def test_valid_values(self):
        """Test all valid overall system status values."""
        assert OverallSystemStatus.OPERATIONAL == "operational"
        assert OverallSystemStatus.DEGRADED == "degraded"
        assert OverallSystemStatus.OUTAGE == "outage"

    def test_string_conversion(self):
        """Test that enum values behave as strings."""
        assert str(OverallSystemStatus.OPERATIONAL) == "operational"
        assert OverallSystemStatus("degraded") == OverallSystemStatus.DEGRADED


# ── StageStatus Tests ───────────────────────────────────────────────


class TestStageStatus:
    """Test StageStatus model."""

    def test_valid_stage_status(self):
        """Test creating a valid stage status."""
        status = StageStatus(
            status=OverallSystemStatus.OPERATIONAL,
            last_success_at=datetime(2026, 3, 26, 4, 15, 0, tzinfo=UTC),
        )
        assert status.status == OverallSystemStatus.OPERATIONAL
        assert status.last_success_at is not None

    def test_stage_status_without_last_success(self):
        """Test stage status when no successful run exists."""
        status = StageStatus(status=OverallSystemStatus.OUTAGE)
        assert status.status == OverallSystemStatus.OUTAGE
        assert status.last_success_at is None

    def test_stage_status_naive_datetime_rejected(self):
        """Test that naive (non-UTC) datetimes are rejected."""
        with pytest.raises(ValidationError, match="timezone-aware"):
            StageStatus(
                status=OverallSystemStatus.OPERATIONAL,
                last_success_at=datetime(2026, 3, 26, 4, 15, 0),
            )

    def test_stage_status_invalid_enum(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValidationError):
            StageStatus(status="invalid_status")


# ── BronzeDailySummary Tests ────────────────────────────────────────


class TestBronzeDailySummary:
    """Test BronzeDailySummary model."""

    def test_valid_bronze_summary(self):
        """Test creating a valid Bronze daily summary."""
        summary = BronzeDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_ingested=450,
        )
        assert summary.status == PipelineStageStatus.SUCCESS
        assert summary.records_ingested == 450

    def test_zero_records_ingested(self):
        """Test Bronze summary with zero records."""
        summary = BronzeDailySummary(
            status=PipelineStageStatus.NO_DATA,
            records_ingested=0,
        )
        assert summary.records_ingested == 0

    def test_negative_records_ingested_rejected(self):
        """Test that negative record counts are rejected."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            BronzeDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_ingested=-1,
            )


# ── SilverDailySummary Tests ────────────────────────────────────────


class TestSilverDailySummary:
    """Test SilverDailySummary model."""

    def test_valid_silver_summary(self):
        """Test creating a valid Silver daily summary."""
        summary = SilverDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_processed=448,
            records_quarantined=2,
            quality_score=0.996,
        )
        assert summary.status == PipelineStageStatus.SUCCESS
        assert summary.records_processed == 448
        assert summary.records_quarantined == 2
        assert summary.quality_score == 0.996

    def test_perfect_quality_score(self):
        """Test quality score at upper boundary (1.0)."""
        summary = SilverDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_processed=100,
            records_quarantined=0,
            quality_score=1.0,
        )
        assert summary.quality_score == 1.0

    def test_zero_quality_score(self):
        """Test quality score at lower boundary (0.0)."""
        summary = SilverDailySummary(
            status=PipelineStageStatus.FAILED,
            records_processed=0,
            records_quarantined=100,
            quality_score=0.0,
        )
        assert summary.quality_score == 0.0

    def test_quality_score_above_one_rejected(self):
        """Test that quality scores above 1.0 are rejected."""
        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 1"
        ):
            SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=100,
                records_quarantined=0,
                quality_score=1.1,
            )

    def test_quality_score_below_zero_rejected(self):
        """Test that negative quality scores are rejected."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=100,
                records_quarantined=0,
                quality_score=-0.1,
            )

    def test_negative_records_processed_rejected(self):
        """Test that negative processed record counts are rejected."""
        with pytest.raises(ValidationError):
            SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=-1,
                records_quarantined=0,
                quality_score=0.5,
            )

    def test_negative_records_quarantined_rejected(self):
        """Test that negative quarantined record counts are rejected."""
        with pytest.raises(ValidationError):
            SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=100,
                records_quarantined=-1,
                quality_score=0.5,
            )


# ── GoldDailySummary Tests ──────────────────────────────────────────


class TestGoldDailySummary:
    """Test GoldDailySummary model."""

    def test_valid_gold_summary(self):
        """Test creating a valid Gold daily summary."""
        summary = GoldDailySummary(
            status=PipelineStageStatus.SUCCESS,
            artifacts_written=312,
        )
        assert summary.status == PipelineStageStatus.SUCCESS
        assert summary.artifacts_written == 312

    def test_zero_artifacts_written(self):
        """Test Gold summary with zero artifacts."""
        summary = GoldDailySummary(
            status=PipelineStageStatus.SKIPPED,
            artifacts_written=0,
        )
        assert summary.artifacts_written == 0

    def test_negative_artifacts_rejected(self):
        """Test that negative artifact counts are rejected."""
        with pytest.raises(ValidationError):
            GoldDailySummary(
                status=PipelineStageStatus.SUCCESS,
                artifacts_written=-1,
            )


# ── DailySummary Tests ──────────────────────────────────────────────


class TestDailySummary:
    """Test DailySummary model."""

    def test_valid_daily_summary(self):
        """Test creating a valid daily summary."""
        summary = DailySummary(
            date=date(2026, 3, 26),
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_ingested=450,
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=448,
                records_quarantined=2,
                quality_score=0.996,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.SUCCESS,
                artifacts_written=312,
            ),
        )
        assert summary.date == date(2026, 3, 26)
        assert summary.bronze.records_ingested == 450
        assert summary.silver.quality_score == 0.996
        assert summary.gold.artifacts_written == 312

    def test_all_failed_daily_summary(self):
        """Test daily summary where all stages failed."""
        summary = DailySummary(
            date=date(2026, 3, 26),
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.FAILED,
                records_ingested=0,
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.FAILED,
                records_processed=0,
                records_quarantined=0,
                quality_score=0.0,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.FAILED,
                artifacts_written=0,
            ),
        )
        assert summary.bronze.status == PipelineStageStatus.FAILED
        assert summary.silver.status == PipelineStageStatus.FAILED
        assert summary.gold.status == PipelineStageStatus.FAILED

    def test_daily_summary_date_from_string(self):
        """Test daily summary accepts date as ISO string."""
        summary = DailySummary(
            date="2026-03-26",
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_ingested=100,
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=100,
                records_quarantined=0,
                quality_score=1.0,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.SUCCESS,
                artifacts_written=50,
            ),
        )
        assert summary.date == date(2026, 3, 26)


# ── PipelineHealthReport Tests ──────────────────────────────────────


def _make_daily_summary(d: date) -> DailySummary:
    """Helper to create a daily summary for a given date."""
    return DailySummary(
        date=d,
        bronze=BronzeDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_ingested=100,
        ),
        silver=SilverDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_processed=98,
            records_quarantined=2,
            quality_score=0.98,
        ),
        gold=GoldDailySummary(
            status=PipelineStageStatus.SUCCESS,
            artifacts_written=50,
        ),
    )


def _make_stages() -> dict[str, StageStatus]:
    """Helper to create a valid stages dict."""
    return {
        "bronze": StageStatus(
            status=OverallSystemStatus.OPERATIONAL,
            last_success_at=datetime(2026, 3, 26, 4, 15, 0, tzinfo=UTC),
        ),
        "silver": StageStatus(
            status=OverallSystemStatus.OPERATIONAL,
            last_success_at=datetime(2026, 3, 26, 4, 45, 0, tzinfo=UTC),
        ),
        "gold": StageStatus(
            status=OverallSystemStatus.OPERATIONAL,
            last_success_at=datetime(2026, 3, 26, 5, 30, 0, tzinfo=UTC),
        ),
    }


class TestPipelineHealthReport:
    """Test PipelineHealthReport model."""

    def test_valid_full_report(self):
        """Test creating a valid full pipeline health report."""
        report = PipelineHealthReport(
            schema_version="1.0.0",
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[
                _make_daily_summary(date(2026, 3, 26)),
                _make_daily_summary(date(2026, 3, 25)),
                _make_daily_summary(date(2026, 3, 24)),
            ],
        )
        assert report.schema_version == "1.0.0"
        assert report.overall_status == OverallSystemStatus.OPERATIONAL
        assert len(report.daily_summaries) == 3
        assert len(report.stages) == 3

    def test_default_schema_version(self):
        """Test that schema_version defaults to 1.0.0."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
        )
        assert report.schema_version == "1.0.0"

    def test_empty_daily_summaries(self):
        """Test report with empty daily summaries list."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[],
        )
        assert report.daily_summaries == []

    def test_max_seven_daily_summaries(self):
        """Test report with maximum 7 daily summaries."""
        summaries = [_make_daily_summary(date(2026, 3, 26 - i)) for i in range(7)]
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=summaries,
        )
        assert len(report.daily_summaries) == 7

    def test_more_than_seven_summaries_rejected(self):
        """Test that more than 7 daily summaries are rejected."""
        summaries = [_make_daily_summary(date(2026, 3, 26 - i)) for i in range(8)]
        with pytest.raises(ValidationError, match="at most 7"):
            PipelineHealthReport(
                generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
                overall_status=OverallSystemStatus.OPERATIONAL,
                stages=_make_stages(),
                daily_summaries=summaries,
            )

    def test_daily_summaries_wrong_order_rejected(self):
        """Test that daily summaries not in descending date order are rejected."""
        with pytest.raises(
            ValidationError, match="daily_summaries must be ordered most-recent first"
        ):
            PipelineHealthReport(
                generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
                overall_status=OverallSystemStatus.OPERATIONAL,
                stages=_make_stages(),
                daily_summaries=[
                    _make_daily_summary(date(2026, 3, 24)),
                    _make_daily_summary(date(2026, 3, 25)),
                    _make_daily_summary(date(2026, 3, 26)),
                ],
            )

    def test_invalid_schema_version_format(self):
        """Test that non-semver schema_version is rejected."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            PipelineHealthReport(
                schema_version="v1.0",
                generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
                overall_status=OverallSystemStatus.OPERATIONAL,
                stages=_make_stages(),
            )

    def test_naive_generated_at_rejected(self):
        """Test that naive datetime for generated_at is rejected."""
        with pytest.raises(ValidationError, match="timezone-aware"):
            PipelineHealthReport(
                generated_at=datetime(2026, 3, 26, 6, 0, 0),
                overall_status=OverallSystemStatus.OPERATIONAL,
                stages=_make_stages(),
            )

    def test_invalid_stage_key_rejected(self):
        """Test that invalid stage keys are rejected."""
        with pytest.raises(ValidationError, match="Invalid stage keys"):
            PipelineHealthReport(
                generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
                overall_status=OverallSystemStatus.OPERATIONAL,
                stages={
                    "bronze": StageStatus(
                        status=OverallSystemStatus.OPERATIONAL,
                    ),
                    "platinum": StageStatus(
                        status=OverallSystemStatus.OPERATIONAL,
                    ),
                },
            )

    def test_partial_stages(self):
        """Test report with only some stages present."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.DEGRADED,
            stages={
                "bronze": StageStatus(
                    status=OverallSystemStatus.OPERATIONAL,
                    last_success_at=datetime(2026, 3, 26, 4, 15, 0, tzinfo=UTC),
                ),
            },
        )
        assert len(report.stages) == 1
        assert "bronze" in report.stages

    def test_outage_report(self):
        """Test report representing a full outage."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OUTAGE,
            stages={
                "bronze": StageStatus(status=OverallSystemStatus.OUTAGE),
                "silver": StageStatus(status=OverallSystemStatus.OUTAGE),
                "gold": StageStatus(status=OverallSystemStatus.OUTAGE),
            },
            daily_summaries=[
                DailySummary(
                    date=date(2026, 3, 26),
                    bronze=BronzeDailySummary(
                        status=PipelineStageStatus.FAILED,
                        records_ingested=0,
                    ),
                    silver=SilverDailySummary(
                        status=PipelineStageStatus.FAILED,
                        records_processed=0,
                        records_quarantined=0,
                        quality_score=0.0,
                    ),
                    gold=GoldDailySummary(
                        status=PipelineStageStatus.FAILED,
                        artifacts_written=0,
                    ),
                ),
            ],
        )
        assert report.overall_status == OverallSystemStatus.OUTAGE


# ── Serialization / Deserialization Round-Trip Tests ────────────────


class TestSerialization:
    """Test serialization and deserialization round-trips."""

    def test_full_report_round_trip(self):
        """Test that a full report survives JSON serialization round-trip."""
        report = PipelineHealthReport(
            schema_version="1.0.0",
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[
                _make_daily_summary(date(2026, 3, 26)),
                _make_daily_summary(date(2026, 3, 25)),
            ],
        )

        json_str = report.model_dump_json()
        restored = PipelineHealthReport.model_validate_json(json_str)

        assert restored.schema_version == report.schema_version
        assert restored.generated_at == report.generated_at
        assert restored.overall_status == report.overall_status
        assert len(restored.daily_summaries) == len(report.daily_summaries)
        assert len(restored.stages) == len(report.stages)

    def test_report_dict_round_trip(self):
        """Test that a report survives dict serialization round-trip."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[_make_daily_summary(date(2026, 3, 26))],
        )

        data = report.model_dump(mode="json")
        restored = PipelineHealthReport.model_validate(data)

        assert restored.schema_version == report.schema_version
        assert restored.overall_status == report.overall_status
        assert (
            restored.daily_summaries[0].bronze.records_ingested
            == report.daily_summaries[0].bronze.records_ingested
        )

    def test_empty_summaries_round_trip(self):
        """Test round-trip with empty daily summaries."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[],
        )

        json_str = report.model_dump_json()
        restored = PipelineHealthReport.model_validate_json(json_str)

        assert restored.daily_summaries == []

    def test_bronze_summary_round_trip(self):
        """Test BronzeDailySummary JSON round-trip."""
        original = BronzeDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_ingested=450,
        )
        json_str = original.model_dump_json()
        restored = BronzeDailySummary.model_validate_json(json_str)
        assert restored.status == original.status
        assert restored.records_ingested == original.records_ingested

    def test_silver_summary_round_trip(self):
        """Test SilverDailySummary JSON round-trip."""
        original = SilverDailySummary(
            status=PipelineStageStatus.SUCCESS,
            records_processed=448,
            records_quarantined=2,
            quality_score=0.996,
        )
        json_str = original.model_dump_json()
        restored = SilverDailySummary.model_validate_json(json_str)
        assert restored.quality_score == original.quality_score

    def test_gold_summary_round_trip(self):
        """Test GoldDailySummary JSON round-trip."""
        original = GoldDailySummary(
            status=PipelineStageStatus.SUCCESS,
            artifacts_written=312,
        )
        json_str = original.model_dump_json()
        restored = GoldDailySummary.model_validate_json(json_str)
        assert restored.artifacts_written == original.artifacts_written

    def test_serialized_json_matches_schema(self):
        """Test that serialized JSON matches expected schema structure."""
        report = PipelineHealthReport(
            schema_version="1.0.0",
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[_make_daily_summary(date(2026, 3, 26))],
        )

        data = report.model_dump(mode="json")

        # Verify top-level keys match the schema
        assert "schema_version" in data
        assert "generated_at" in data
        assert "overall_status" in data
        assert "stages" in data
        assert "daily_summaries" in data

        # Verify nested structure
        assert "bronze" in data["stages"]
        assert "status" in data["stages"]["bronze"]
        assert "date" in data["daily_summaries"][0]
        assert "bronze" in data["daily_summaries"][0]
        assert "silver" in data["daily_summaries"][0]
        assert "gold" in data["daily_summaries"][0]

    def test_enum_values_serialized_as_strings(self):
        """Test that enum values serialize as plain strings."""
        report = PipelineHealthReport(
            generated_at=datetime(2026, 3, 26, 6, 0, 0, tzinfo=UTC),
            overall_status=OverallSystemStatus.OPERATIONAL,
            stages=_make_stages(),
            daily_summaries=[_make_daily_summary(date(2026, 3, 26))],
        )

        data = report.model_dump(mode="json")

        assert data["overall_status"] == "operational"
        assert data["stages"]["bronze"]["status"] == "operational"
        assert data["daily_summaries"][0]["bronze"]["status"] == "success"


# ── Schema Generation Tests ─────────────────────────────────────────


class TestSchemaGeneration:
    """Test JSON schema generation for health models."""

    def test_pipeline_health_report_schema(self):
        """Test that PipelineHealthReport generates a valid JSON schema."""
        schema = PipelineHealthReport.model_json_schema()
        assert schema["title"] == "PipelineHealthReport"
        assert "properties" in schema

    def test_schema_includes_all_top_level_fields(self):
        """Test that schema includes all expected top-level fields."""
        schema = PipelineHealthReport.model_json_schema()
        props = schema["properties"]
        expected_fields = {
            "schema_version",
            "generated_at",
            "overall_status",
            "stages",
            "daily_summaries",
        }
        assert expected_fields.issubset(set(props.keys()))
