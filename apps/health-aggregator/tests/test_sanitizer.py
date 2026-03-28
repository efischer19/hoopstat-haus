"""
Security-focused tests for the sanitizer module.

Validates all sanitization rules with adversarial test cases per the
acceptance criteria in the health-aggregator sanitization issue.

Test categories:
  - _sanitize_stage_status: enum allowlist for PipelineStageStatus
  - _sanitize_overall_status: enum allowlist for OverallSystemStatus
  - _sanitize_iso_utc_timestamp: ISO 8601 UTC validation
  - _sanitize_count: non-negative integer enforcement
  - _sanitize_quality_score: [0.0, 1.0] clamp
  - _reconstruct_stage_status_dict: allowlist field extraction for stages
  - _reconstruct_daily_summary_dict: allowlist field extraction for summaries
  - _reconstruct_allowlisted_dict: full Pass-1 reconstruction
  - _contains_secrets: adversarial pattern matching
  - sanitize_report (integration): end-to-end clean-pass and fallback paths
"""

import datetime as dt
from unittest.mock import patch

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

from app.sanitizer import (
    _contains_secrets,
    _make_fallback_report,
    _reconstruct_allowlisted_dict,
    _reconstruct_daily_summary_dict,
    _reconstruct_stage_status_dict,
    _sanitize_count,
    _sanitize_iso_utc_timestamp,
    _sanitize_overall_status,
    _sanitize_quality_score,
    _sanitize_stage_status,
    sanitize_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    overall_status: OverallSystemStatus = OverallSystemStatus.OPERATIONAL,
    stages: dict | None = None,
    daily_summaries: list | None = None,
    generated_at: dt.datetime | None = None,
) -> PipelineHealthReport:
    """Construct a minimal valid PipelineHealthReport for testing."""
    return PipelineHealthReport(
        generated_at=generated_at or dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC),
        overall_status=overall_status,
        stages=stages if stages is not None else {},
        daily_summaries=daily_summaries if daily_summaries is not None else [],
    )


def _make_full_report() -> PipelineHealthReport:
    """Construct a fully-populated 3-day PipelineHealthReport for testing."""
    today = dt.date(2024, 1, 15)
    generated_at = dt.datetime(2024, 1, 15, 12, 0, 0, tzinfo=dt.UTC)

    summaries = []
    for i in range(3):
        d = today - dt.timedelta(days=i)
        summaries.append(
            DailySummary(
                date=d,
                bronze=BronzeDailySummary(
                    status=PipelineStageStatus.SUCCESS, records_ingested=100
                ),
                silver=SilverDailySummary(
                    status=PipelineStageStatus.SUCCESS,
                    records_processed=90,
                    records_quarantined=10,
                    quality_score=0.9,
                ),
                gold=GoldDailySummary(
                    status=PipelineStageStatus.SUCCESS, artifacts_written=5
                ),
            )
        )

    stages = {
        "bronze": StageStatus(
            status=OverallSystemStatus.OPERATIONAL, last_success_at=generated_at
        ),
        "silver": StageStatus(
            status=OverallSystemStatus.OPERATIONAL, last_success_at=generated_at
        ),
        "gold": StageStatus(
            status=OverallSystemStatus.OPERATIONAL, last_success_at=generated_at
        ),
    }

    return PipelineHealthReport(
        generated_at=generated_at,
        overall_status=OverallSystemStatus.OPERATIONAL,
        stages=stages,
        daily_summaries=summaries,
    )


# ---------------------------------------------------------------------------
# _sanitize_stage_status
# ---------------------------------------------------------------------------


class TestSanitizeStageStatus:
    def test_success_permitted(self):
        assert _sanitize_stage_status("success") == "success"

    def test_failed_permitted(self):
        assert _sanitize_stage_status("failed") == "failed"

    def test_skipped_permitted(self):
        assert _sanitize_stage_status("skipped") == "skipped"

    def test_no_data_permitted(self):
        assert _sanitize_stage_status("no_data") == "no_data"

    def test_unknown_maps_to_failed(self):
        assert _sanitize_stage_status("some_secret_status") == "failed"

    def test_empty_string_maps_to_failed(self):
        assert _sanitize_stage_status("") == "failed"

    def test_none_maps_to_failed(self):
        assert _sanitize_stage_status(None) == "failed"

    def test_arn_injection_maps_to_failed(self):
        assert _sanitize_stage_status("arn:aws:iam::123456789012:role/Role") == "failed"

    def test_integer_input_maps_to_failed(self):
        assert _sanitize_stage_status(42) == "failed"

    def test_uppercase_rejected(self):
        # Enum values are lowercase; uppercase should not pass
        assert _sanitize_stage_status("SUCCESS") == "failed"


# ---------------------------------------------------------------------------
# _sanitize_overall_status
# ---------------------------------------------------------------------------


class TestSanitizeOverallStatus:
    def test_operational_permitted(self):
        assert _sanitize_overall_status("operational") == "operational"

    def test_degraded_permitted(self):
        assert _sanitize_overall_status("degraded") == "degraded"

    def test_outage_permitted(self):
        assert _sanitize_overall_status("outage") == "outage"

    def test_unknown_maps_to_degraded(self):
        assert _sanitize_overall_status("OPERATIONAL") == "degraded"

    def test_empty_string_maps_to_degraded(self):
        assert _sanitize_overall_status("") == "degraded"

    def test_none_maps_to_degraded(self):
        assert _sanitize_overall_status(None) == "degraded"

    def test_arn_injection_maps_to_degraded(self):
        assert (
            _sanitize_overall_status("arn:aws:iam::123456789012:role/R") == "degraded"
        )


# ---------------------------------------------------------------------------
# _sanitize_iso_utc_timestamp
# ---------------------------------------------------------------------------


class TestSanitizeIsoUtcTimestamp:
    def test_z_suffix_accepted(self):
        result = _sanitize_iso_utc_timestamp("2024-01-15T00:00:00Z")
        assert result == "2024-01-15T00:00:00Z"

    def test_plus_zero_offset_accepted(self):
        result = _sanitize_iso_utc_timestamp("2024-01-15T00:00:00+00:00")
        assert result == "2024-01-15T00:00:00Z"

    def test_datetime_object_utc_accepted(self):
        ts = dt.datetime(2024, 1, 15, 12, 30, 0, tzinfo=dt.UTC)
        result = _sanitize_iso_utc_timestamp(ts)
        assert result == "2024-01-15T12:30:00Z"

    def test_none_returns_none(self):
        assert _sanitize_iso_utc_timestamp(None) is None

    def test_naive_datetime_rejected(self):
        ts = dt.datetime(2024, 1, 15, 12, 0, 0)  # no tzinfo
        assert _sanitize_iso_utc_timestamp(ts) is None

    def test_non_utc_timezone_rejected(self):
        eastern = dt.timezone(dt.timedelta(hours=-5))
        ts = dt.datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)
        assert _sanitize_iso_utc_timestamp(ts) is None

    def test_non_utc_string_rejected(self):
        assert _sanitize_iso_utc_timestamp("2024-01-15T00:00:00-05:00") is None

    def test_invalid_string_rejected(self):
        assert _sanitize_iso_utc_timestamp("not-a-timestamp") is None

    def test_integer_rejected(self):
        assert _sanitize_iso_utc_timestamp(1705276800) is None

    def test_output_has_z_suffix(self):
        result = _sanitize_iso_utc_timestamp("2024-06-01T08:00:00+00:00")
        assert result is not None
        assert result.endswith("Z")


# ---------------------------------------------------------------------------
# _sanitize_count
# ---------------------------------------------------------------------------


class TestSanitizeCount:
    def test_positive_int(self):
        assert _sanitize_count(42) == 42

    def test_zero(self):
        assert _sanitize_count(0) == 0

    def test_negative_clamped_to_zero(self):
        assert _sanitize_count(-5) == 0

    def test_float_truncated(self):
        assert _sanitize_count(3.9) == 3

    def test_string_int(self):
        assert _sanitize_count("100") == 100

    def test_none_returns_zero(self):
        assert _sanitize_count(None) == 0

    def test_non_numeric_string_returns_zero(self):
        assert _sanitize_count("not_a_number") == 0

    def test_very_large_number_accepted(self):
        assert _sanitize_count(10_000_000) == 10_000_000


# ---------------------------------------------------------------------------
# _sanitize_quality_score
# ---------------------------------------------------------------------------


class TestSanitizeQualityScore:
    def test_perfect_score(self):
        assert _sanitize_quality_score(1.0) == pytest.approx(1.0)

    def test_zero_score(self):
        assert _sanitize_quality_score(0.0) == pytest.approx(0.0)

    def test_mid_range(self):
        assert _sanitize_quality_score(0.75) == pytest.approx(0.75)

    def test_above_one_clamped(self):
        assert _sanitize_quality_score(1.5) == pytest.approx(1.0)

    def test_negative_clamped_to_zero(self):
        assert _sanitize_quality_score(-0.1) == pytest.approx(0.0)

    def test_none_returns_zero(self):
        assert _sanitize_quality_score(None) == pytest.approx(0.0)

    def test_non_numeric_returns_zero(self):
        assert _sanitize_quality_score("abc") == pytest.approx(0.0)

    def test_string_float(self):
        assert _sanitize_quality_score("0.95") == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# _reconstruct_stage_status_dict
# ---------------------------------------------------------------------------


class TestReconstructStageStatusDict:
    def test_pydantic_model_input(self):
        stage = StageStatus(
            status=OverallSystemStatus.OPERATIONAL,
            last_success_at=dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC),
        )
        result = _reconstruct_stage_status_dict(stage)
        assert result["status"] == "operational"
        assert result["last_success_at"] == "2024-01-15T00:00:00Z"

    def test_dict_input(self):
        stage = {"status": "degraded", "last_success_at": "2024-01-15T00:00:00Z"}
        result = _reconstruct_stage_status_dict(stage)
        assert result["status"] == "degraded"

    def test_none_last_success_omitted(self):
        stage = StageStatus(status=OverallSystemStatus.OUTAGE, last_success_at=None)
        result = _reconstruct_stage_status_dict(stage)
        assert "last_success_at" not in result

    def test_invalid_status_replaced_with_degraded(self):
        stage = {"status": "UNKNOWN_STATUS_XYZ"}
        result = _reconstruct_stage_status_dict(stage)
        assert result["status"] == "degraded"

    def test_extra_fields_excluded(self):
        stage = {
            "status": "operational",
            "last_success_at": "2024-01-15T00:00:00Z",
            "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:MyFn",
            "log_stream": "/aws/lambda/my-function/2024/01/15",
        }
        result = _reconstruct_stage_status_dict(stage)
        assert "lambda_arn" not in result
        assert "log_stream" not in result


# ---------------------------------------------------------------------------
# _reconstruct_daily_summary_dict
# ---------------------------------------------------------------------------


class TestReconstructDailySummaryDict:
    def test_pydantic_model_input(self):
        summary = DailySummary(
            date=dt.date(2024, 1, 15),
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.SUCCESS, records_ingested=100
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=90,
                records_quarantined=10,
                quality_score=0.9,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.SUCCESS, artifacts_written=5
            ),
        )
        result = _reconstruct_daily_summary_dict(summary)
        assert result is not None
        assert result["date"] == "2024-01-15"
        assert result["bronze"]["status"] == "success"
        assert result["bronze"]["records_ingested"] == 100
        assert result["silver"]["quality_score"] == pytest.approx(0.9)
        assert result["gold"]["artifacts_written"] == 5

    def test_invalid_date_returns_none(self):
        result = _reconstruct_daily_summary_dict({"date": "not-a-date"})
        assert result is None

    def test_missing_date_returns_none(self):
        result = _reconstruct_daily_summary_dict({})
        assert result is None

    def test_unknown_stage_status_replaced_with_failed(self):
        summary = {
            "date": "2024-01-15",
            "bronze": {"status": "INJECTED_VALUE", "records_ingested": 0},
            "silver": {
                "status": "success",
                "records_processed": 0,
                "records_quarantined": 0,
                "quality_score": 1.0,
            },
            "gold": {"status": "success", "artifacts_written": 0},
        }
        result = _reconstruct_daily_summary_dict(summary)
        assert result is not None
        assert result["bronze"]["status"] == "failed"

    def test_out_of_range_quality_score_clamped(self):
        summary = {
            "date": "2024-01-15",
            "bronze": {"status": "success", "records_ingested": 0},
            "silver": {
                "status": "success",
                "records_processed": 0,
                "records_quarantined": 0,
                "quality_score": 999.9,  # way out of range
            },
            "gold": {"status": "success", "artifacts_written": 0},
        }
        result = _reconstruct_daily_summary_dict(summary)
        assert result is not None
        assert result["silver"]["quality_score"] == pytest.approx(1.0)

    def test_negative_count_clamped_to_zero(self):
        summary = {
            "date": "2024-01-15",
            "bronze": {"status": "success", "records_ingested": -50},
            "silver": {
                "status": "success",
                "records_processed": -10,
                "records_quarantined": 0,
                "quality_score": 0.5,
            },
            "gold": {"status": "success", "artifacts_written": 0},
        }
        result = _reconstruct_daily_summary_dict(summary)
        assert result is not None
        assert result["bronze"]["records_ingested"] == 0
        assert result["silver"]["records_processed"] == 0

    def test_extra_fields_excluded(self):
        summary = DailySummary(
            date=dt.date(2024, 1, 15),
            bronze=BronzeDailySummary(
                status=PipelineStageStatus.SUCCESS, records_ingested=0
            ),
            silver=SilverDailySummary(
                status=PipelineStageStatus.SUCCESS,
                records_processed=0,
                records_quarantined=0,
                quality_score=1.0,
            ),
            gold=GoldDailySummary(
                status=PipelineStageStatus.SUCCESS, artifacts_written=0
            ),
        )
        result = _reconstruct_daily_summary_dict(summary)
        assert result is not None
        # Only permitted top-level keys present
        assert set(result.keys()) == {"date", "bronze", "silver", "gold"}
        # No start_time / duration fields
        assert "start_time" not in result
        assert "duration_seconds" not in result


# ---------------------------------------------------------------------------
# _reconstruct_allowlisted_dict
# ---------------------------------------------------------------------------


class TestReconstructAllowlistedDict:
    def test_clean_report_fields_preserved(self):
        report = _make_full_report()
        result = _reconstruct_allowlisted_dict(report)

        assert result["schema_version"] == "1.0.0"
        assert result["overall_status"] == "operational"
        assert "generated_at" in result
        assert len(result["daily_summaries"]) == 3

    def test_only_permitted_top_level_keys(self):
        report = _make_full_report()
        result = _reconstruct_allowlisted_dict(report)
        permitted = {
            "schema_version",
            "generated_at",
            "overall_status",
            "stages",
            "daily_summaries",
        }
        assert set(result.keys()) == permitted

    def test_generated_at_normalised_to_z_suffix(self):
        report = _make_report(
            generated_at=dt.datetime(2024, 6, 1, 8, 0, 0, tzinfo=dt.UTC)
        )
        result = _reconstruct_allowlisted_dict(report)
        assert result["generated_at"].endswith("Z")

    def test_stages_only_permitted_keys(self):
        report = _make_full_report()
        result = _reconstruct_allowlisted_dict(report)
        for key in result["stages"]:
            assert key in {"bronze", "silver", "gold"}

    def test_no_start_times_or_durations(self):
        """Execution window obfuscation: only completion timestamps retained."""
        report = _make_full_report()
        result = _reconstruct_allowlisted_dict(report)
        json_str = str(result)
        assert "start_time" not in json_str
        assert "duration" not in json_str
        assert "billed_duration" not in json_str
        assert "request_id" not in json_str


# ---------------------------------------------------------------------------
# _contains_secrets — adversarial inputs
# ---------------------------------------------------------------------------


class TestContainsSecrets:
    def test_clean_payload_not_flagged(self):
        clean_json = '{"overall_status":"operational","schema_version":"1.0.0"}'
        assert _contains_secrets(clean_json) is False

    # AWS access key IDs
    def test_aws_access_key_detected(self):
        payload = '{"key":"AKIAIOSFODNN7EXAMPLE"}'
        assert _contains_secrets(payload) is True

    def test_aws_access_key_another_variant(self):
        # A different valid 20-char AWS access key (AKIA + 16 uppercase alphanumerics)
        payload = '{"config":"AKIAI44QH8DHBEXAMPLE"}'  # 20-char valid key
        assert _contains_secrets(payload) is True

    # AWS ARNs
    def test_arn_iam_role_detected(self):
        payload = '{"msg":"arn:aws:iam::123456789012:role/MyRole"}'
        assert _contains_secrets(payload) is True

    def test_arn_lambda_detected(self):
        payload = '{"fn":"arn:aws:lambda:us-east-1:123456789012:function:Fn"}'
        assert _contains_secrets(payload) is True

    def test_arn_s3_detected(self):
        payload = '{"r":"arn:aws:s3:us-east-1:123456789012:bucket/b"}'
        assert _contains_secrets(payload) is True

    # AWS session tokens
    def test_session_token_detected(self):
        payload = '{"token":"FwoGZXIvYXdzEJr//////////wEaD' + "A" * 40 + '"}'
        assert _contains_secrets(payload) is True

    # RFC 1918 internal IPs
    def test_internal_ip_10_detected(self):
        assert _contains_secrets('{"host":"10.0.1.5"}') is True

    def test_internal_ip_172_detected(self):
        assert _contains_secrets('{"host":"172.16.0.1"}') is True

    def test_internal_ip_172_31_detected(self):
        assert _contains_secrets('{"host":"172.31.255.254"}') is True

    def test_internal_ip_192_168_detected(self):
        assert _contains_secrets('{"host":"192.168.1.100"}') is True

    def test_public_ip_not_flagged(self):
        # 8.8.8.8 is a public IP and should not be flagged
        assert _contains_secrets('{"dns":"8.8.8.8"}') is False

    def test_172_15_not_flagged(self):
        # 172.15.x.x is NOT in the RFC 1918 range
        assert _contains_secrets('{"host":"172.15.0.1"}') is False

    def test_172_32_not_flagged(self):
        # 172.32.x.x is NOT in the RFC 1918 range
        assert _contains_secrets('{"host":"172.32.0.1"}') is False

    # Bearer tokens
    def test_bearer_token_detected(self):
        assert (
            _contains_secrets('{"auth":"Bearer eyJhbGciOiJSUzI1NiJ9.payload"}') is True
        )

    # Secret key reference patterns
    def test_aws_secret_key_reference_detected(self):
        assert _contains_secrets('{"aws_secret_access_key":"abc123"}') is True

    def test_secret_access_key_detected(self):
        assert _contains_secrets('{"secret_access_key":"abc123"}') is True


# ---------------------------------------------------------------------------
# _make_fallback_report
# ---------------------------------------------------------------------------


class TestMakeFallbackReport:
    def test_fallback_is_valid_pydantic_model(self):
        ts = dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC)
        fallback = _make_fallback_report(ts)
        assert isinstance(fallback, PipelineHealthReport)

    def test_fallback_status_is_degraded(self):
        ts = dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC)
        fallback = _make_fallback_report(ts)
        assert fallback.overall_status == OverallSystemStatus.DEGRADED

    def test_fallback_stages_is_empty(self):
        ts = dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC)
        fallback = _make_fallback_report(ts)
        assert fallback.stages == {}

    def test_fallback_daily_summaries_is_empty(self):
        ts = dt.datetime(2024, 1, 15, 0, 0, 0, tzinfo=dt.UTC)
        fallback = _make_fallback_report(ts)
        assert fallback.daily_summaries == []

    def test_fallback_preserves_generated_at(self):
        ts = dt.datetime(2024, 6, 15, 10, 30, 0, tzinfo=dt.UTC)
        fallback = _make_fallback_report(ts)
        assert fallback.generated_at == ts


# ---------------------------------------------------------------------------
# sanitize_report — integration tests
# ---------------------------------------------------------------------------


class TestSanitizeReport:
    def test_clean_report_passes_through(self):
        report = _make_full_report()
        result = sanitize_report(report)
        assert isinstance(result, PipelineHealthReport)
        assert result.overall_status == OverallSystemStatus.OPERATIONAL

    def test_clean_report_returns_original_object(self):
        report = _make_full_report()
        result = sanitize_report(report)
        assert result is report

    def test_clean_report_with_empty_stages(self):
        report = _make_report()
        result = sanitize_report(report)
        assert isinstance(result, PipelineHealthReport)

    def test_return_type_is_always_pipeline_health_report(self):
        """Even when the secret scan triggers, a PipelineHealthReport is returned."""
        report = _make_full_report()
        with patch("app.sanitizer._contains_secrets", return_value=True):
            result = sanitize_report(report)
        assert isinstance(result, PipelineHealthReport)

    def test_secret_detection_triggers_fallback(self):
        """When _contains_secrets returns True, a degraded fallback is returned."""
        report = _make_full_report()
        with patch("app.sanitizer._contains_secrets", return_value=True):
            result = sanitize_report(report)
        assert result.overall_status == OverallSystemStatus.DEGRADED
        assert result.stages == {}
        assert result.daily_summaries == []

    def test_secret_detection_preserves_generated_at_in_fallback(self):
        """Fallback uses the same generated_at timestamp."""
        ts = dt.datetime(2024, 6, 1, 8, 0, 0, tzinfo=dt.UTC)
        report = _make_report(generated_at=ts)
        with patch("app.sanitizer._contains_secrets", return_value=True):
            result = sanitize_report(report)
        assert result.generated_at == ts

    def test_daily_summaries_fields_only_permitted(self):
        report = _make_full_report()
        result = sanitize_report(report)
        assert isinstance(result, PipelineHealthReport)
        for summary in result.daily_summaries:
            # No unexpected attributes should exist
            assert hasattr(summary, "date")
            assert hasattr(summary, "bronze")
            assert hasattr(summary, "silver")
            assert hasattr(summary, "gold")

    def test_stage_status_values_are_valid_enums(self):
        report = _make_full_report()
        result = sanitize_report(report)
        for stage in result.stages.values():
            assert stage.status in OverallSystemStatus

    def test_quality_score_in_range(self):
        report = _make_full_report()
        result = sanitize_report(report)
        for summary in result.daily_summaries:
            assert 0.0 <= summary.silver.quality_score <= 1.0

    def test_counts_are_non_negative(self):
        report = _make_full_report()
        result = sanitize_report(report)
        for summary in result.daily_summaries:
            assert summary.bronze.records_ingested >= 0
            assert summary.silver.records_processed >= 0
            assert summary.silver.records_quarantined >= 0
            assert summary.gold.artifacts_written >= 0

    def test_no_stack_traces_in_output(self):
        """Stack trace keywords must never appear in the serialised report."""
        report = _make_full_report()
        result = sanitize_report(report)
        import json

        json_str = json.dumps(result.model_dump(mode="json"))
        forbidden = ["Traceback", "Exception", "Error:", "raise ", 'File "']
        for token in forbidden:
            assert token not in json_str

    def test_no_internal_metadata_in_output(self):
        """Lambda metadata fields must never appear in the serialised report."""
        report = _make_full_report()
        result = sanitize_report(report)
        import json

        json_str = json.dumps(result.model_dump(mode="json"))
        forbidden_keys = [
            "request_id",
            "log_stream",
            "container_id",
            "billed_duration",
            "memory_used",
            "function_arn",
        ]
        for key in forbidden_keys:
            assert key not in json_str
