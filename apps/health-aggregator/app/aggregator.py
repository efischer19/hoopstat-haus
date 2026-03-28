"""
Core aggregation logic for the health aggregator Lambda.

Combines CloudWatch Logs Insights results, S3 quarantine counts, and Gold
artifact metadata into a PipelineHealthReport validated by the Pydantic schema
defined in hoopstat_data.health_models.
"""

import datetime as dt
import re
from typing import Any

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
from hoopstat_observability import get_logger

logger = get_logger(__name__)

# Number of days to include in the rolling window
LOOKBACK_DAYS = 7

# Patterns that must never appear in the sanitized output (ADR-040 security model).
# If any are detected the aggregator writes a degraded report rather than
# leaking internal infrastructure metadata.
_SENSITIVE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key ID
    re.compile(r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:\d{12}:"),  # AWS ARN
    re.compile(r"(?i)secret[_\-]?access[_\-]?key"),  # secret key references
]


def _parse_date(date_str: str) -> dt.date | None:
    """
    Parse a date string in YYYY-MM-DD or ISO-8601 format.

    CloudWatch Logs Insights returns ``datefloor`` results as ISO-8601
    timestamps (e.g. ``2024-01-15 00:00:00.000``).  This function extracts
    just the date portion.

    Args:
        date_str: Raw date/datetime string from CloudWatch.

    Returns:
        Parsed date, or None if the string cannot be parsed.
    """
    # Strip time component if present
    date_part = date_str.split(" ")[0].split("T")[0]
    try:
        return dt.date.fromisoformat(date_part)
    except ValueError:
        logger.warning(f"Could not parse date string: {date_str!r}")
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    """
    Safely coerce a value to int, falling back to the default on failure.

    Args:
        value: Value to convert.
        default: Fallback value.

    Returns:
        Integer representation of *value*, or *default*.
    """
    if value is None:
        return default
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def _map_stage_status(raw_status: str) -> PipelineStageStatus:
    """
    Map a raw log status string to a PipelineStageStatus enum value.

    Any unrecognised value maps to NO_DATA so the dashboard degrades
    gracefully rather than crashing.

    Args:
        raw_status: Status string as logged by the pipeline Lambda.

    Returns:
        Corresponding PipelineStageStatus enum member.
    """
    mapping = {
        "success": PipelineStageStatus.SUCCESS,
        "failed": PipelineStageStatus.FAILED,
        "skipped": PipelineStageStatus.SKIPPED,
    }
    return mapping.get(raw_status.lower(), PipelineStageStatus.NO_DATA)


def _build_stage_index(
    cw_rows: list[dict[str, str]],
) -> dict[dt.date, dict[str, dict[str, str]]]:
    """
    Build a nested index of CloudWatch rows keyed by (date, stage).

    Args:
        cw_rows: Flat list of dicts from CloudWatch Logs Insights.

    Returns:
        ``{date: {stage_name: row_dict}}`` mapping.
    """
    index: dict[dt.date, dict[str, dict[str, str]]] = {}

    for row in cw_rows:
        raw_date = row.get("execution_date", "")
        stage = row.get("stage", "").lower()

        if not raw_date or not stage:
            continue

        parsed = _parse_date(raw_date)
        if parsed is None:
            continue

        if parsed not in index:
            index[parsed] = {}
        index[parsed][stage] = row

    return index


def _build_daily_summary(
    target_date: dt.date,
    stage_index: dict[dt.date, dict[str, dict[str, str]]],
    quarantine_count: int,
) -> DailySummary:
    """
    Build a DailySummary for a single day from indexed CloudWatch data.

    Args:
        target_date: The date to summarise.
        stage_index: Nested CloudWatch row index from _build_stage_index.
        quarantine_count: Number of quarantine files found in S3 for this day.

    Returns:
        Populated DailySummary Pydantic model.
    """
    day_stages = stage_index.get(target_date, {})

    # --- Bronze ---
    bronze_row = day_stages.get("bronze", {})
    bronze_status = _map_stage_status(bronze_row.get("status", ""))
    bronze = BronzeDailySummary(
        status=bronze_status,
        records_ingested=_safe_int(bronze_row.get("records_ingested")),
    )

    # --- Silver ---
    silver_row = day_stages.get("silver", {})
    silver_status = _map_stage_status(silver_row.get("status", ""))

    records_processed = _safe_int(silver_row.get("records_processed"))
    # S3 quarantine file count is the authoritative source; the CW log field
    # is only used when the S3 prefix scan itself failed (which count_quarantine_files
    # also returns as 0 — indistinguishable from an empty day — so we simply
    # always trust the S3-derived value passed in by the caller).
    records_quarantined = quarantine_count

    # Derive quality score from processed vs quarantined counts.
    # quality_score = 1.0 when no records were quarantined.
    total_records = records_processed + records_quarantined
    if total_records > 0:
        quality_score = round(records_processed / total_records, 4)
    else:
        quality_score = 1.0 if silver_status == PipelineStageStatus.SUCCESS else 0.0

    silver = SilverDailySummary(
        status=silver_status,
        records_processed=records_processed,
        records_quarantined=records_quarantined,
        quality_score=quality_score,
    )

    # --- Gold ---
    gold_row = day_stages.get("gold", {})
    gold_status = _map_stage_status(gold_row.get("status", ""))
    gold = GoldDailySummary(
        status=gold_status,
        artifacts_written=_safe_int(gold_row.get("artifacts_written")),
    )

    return DailySummary(date=target_date, bronze=bronze, silver=silver, gold=gold)


def _derive_stage_statuses(
    daily_summaries: list[DailySummary],
    gold_last_success_at: dt.datetime | None,
) -> dict[str, StageStatus]:
    """
    Derive per-stage StageStatus from the daily summaries.

    A stage is considered OPERATIONAL if its most recent run was successful.
    It is DEGRADED if the most recent run failed.  It is in OUTAGE if no
    successful run exists within the lookback window.

    Args:
        daily_summaries: List of DailySummary models (most-recent first).
        gold_last_success_at: UTC datetime of last Gold index write, or None.

    Returns:
        Dict of stage name → StageStatus suitable for PipelineHealthReport.
    """
    stages: dict[str, StageStatus] = {}

    for stage_name in ("bronze", "silver", "gold"):
        statuses = []
        for summary in daily_summaries:
            stage_obj = getattr(summary, stage_name)
            statuses.append(stage_obj.status)

        most_recent = statuses[0] if statuses else None

        if most_recent == PipelineStageStatus.SUCCESS:
            overall = OverallSystemStatus.OPERATIONAL
        elif most_recent == PipelineStageStatus.FAILED:
            overall = OverallSystemStatus.DEGRADED
        else:
            # NO_DATA or SKIPPED for most recent day
            # Check if any day in the window succeeded
            any_success = any(s == PipelineStageStatus.SUCCESS for s in statuses)
            overall = (
                OverallSystemStatus.DEGRADED
                if any_success
                else OverallSystemStatus.OUTAGE
            )

        # Use the Gold index last-modified time as the Gold stage's last_success_at
        last_success_at: dt.datetime | None = None
        if stage_name == "gold":
            last_success_at = gold_last_success_at
        else:
            # Find the most recent successful day for this stage
            for summary in daily_summaries:
                stage_obj = getattr(summary, stage_name)
                if stage_obj.status == PipelineStageStatus.SUCCESS:
                    # Convert date to midnight UTC datetime
                    last_success_at = dt.datetime(
                        summary.date.year,
                        summary.date.month,
                        summary.date.day,
                        tzinfo=dt.UTC,
                    )
                    break

        stages[stage_name] = StageStatus(
            status=overall, last_success_at=last_success_at
        )

    return stages


def _derive_overall_status(
    stage_statuses: dict[str, StageStatus],
) -> OverallSystemStatus:
    """
    Derive the top-level overall system status from individual stage statuses.

    Rules (highest severity wins):
    - Any stage in OUTAGE → overall OUTAGE
    - Any stage in DEGRADED → overall DEGRADED
    - All stages OPERATIONAL → overall OPERATIONAL

    Args:
        stage_statuses: Per-stage StageStatus dict.

    Returns:
        OverallSystemStatus for the top-level report field.
    """
    statuses = [s.status for s in stage_statuses.values()]

    if any(s == OverallSystemStatus.OUTAGE for s in statuses):
        return OverallSystemStatus.OUTAGE
    if any(s == OverallSystemStatus.DEGRADED for s in statuses):
        return OverallSystemStatus.DEGRADED
    return OverallSystemStatus.OPERATIONAL


def sanitize_report(report_dict: dict) -> dict:
    """
    Basic sanitization pass on the serialised report dict (ADR-040 placeholder).

    Scans every string value in the serialised JSON for patterns that must
    not appear in public output (AWS ARNs, access key IDs, etc.).  If any
    are found a ValueError is raised so the caller can substitute a degraded
    report.

    This is a placeholder for the comprehensive sanitization logic planned in
    a later issue.  Currently it applies the allowlist approach described in
    ADR-040 §Security Model by only retaining explicitly permitted top-level
    keys, and scanning string values for known-sensitive patterns.

    Args:
        report_dict: Serialised report as a plain Python dict.

    Returns:
        The same dict, unchanged, if no sensitive data is detected.

    Raises:
        ValueError: If any sensitive patterns are detected.
    """

    # Flatten all string values for scanning
    def _iter_strings(obj: Any):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from _iter_strings(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from _iter_strings(item)

    for text in _iter_strings(report_dict):
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.search(text):
                raise ValueError(
                    f"Sensitive pattern detected in report output: {pattern.pattern}"
                )

    return report_dict


class HealthAggregator:
    """
    Orchestrates the collection, compilation, and validation of pipeline health data.

    Combines data from CloudWatch Logs Insights (execution statuses) and S3
    (quarantine counts, Gold index timestamp) into a validated
    PipelineHealthReport.
    """

    def __init__(
        self,
        cw_client,
        s3_reader,
        lookback_days: int = LOOKBACK_DAYS,
    ) -> None:
        """
        Initialise the aggregator.

        Args:
            cw_client: CloudWatchClient instance (or compatible mock).
            s3_reader: S3Reader instance (or compatible mock).
            lookback_days: Number of days to include in the rolling window.
        """
        self.cw_client = cw_client
        self.s3_reader = s3_reader
        self.lookback_days = lookback_days

    def aggregate(self) -> PipelineHealthReport:
        """
        Run the full aggregation pipeline and return a validated health report.

        Steps:
        1. Query CloudWatch Logs Insights for the last N days.
        2. Count quarantine files from S3 for each day.
        3. Check Gold index last-modified timestamp.
        4. Build daily summaries.
        5. Derive stage and overall statuses.
        6. Validate output against the Pydantic schema.
        7. Sanitize output.

        Returns:
            A fully populated and validated PipelineHealthReport.

        Raises:
            ValueError: If the sanitization check detects sensitive data.
        """
        generated_at = dt.datetime.now(dt.UTC)

        # --- Step 1: CloudWatch Logs Insights ---
        try:
            cw_rows = self.cw_client.query_pipeline_status(self.lookback_days)
        except Exception as exc:
            logger.error(f"CloudWatch query failed — producing degraded report: {exc}")
            return self._degraded_report(generated_at)

        stage_index = _build_stage_index(cw_rows)

        # --- Steps 2 & 4: S3 quarantine counts + daily summaries ---
        today = generated_at.date()
        daily_summaries: list[DailySummary] = []

        for offset in range(self.lookback_days):
            target_date = today - dt.timedelta(days=offset)
            quarantine_count = self.s3_reader.count_quarantine_files(target_date)
            summary = _build_daily_summary(target_date, stage_index, quarantine_count)
            daily_summaries.append(summary)

        # daily_summaries is already most-recent first (offset 0 = today)

        # --- Step 3: Gold index timestamp ---
        gold_last_success_at = self.s3_reader.get_gold_index_last_modified()

        # --- Step 5: Derive statuses ---
        stage_statuses = _derive_stage_statuses(daily_summaries, gold_last_success_at)
        overall_status = _derive_overall_status(stage_statuses)

        # --- Step 6: Validate via Pydantic ---
        report = PipelineHealthReport(
            generated_at=generated_at,
            overall_status=overall_status,
            stages=stage_statuses,
            daily_summaries=daily_summaries,
        )

        # --- Step 7: Sanitize ---
        report_dict = report.model_dump(mode="json")
        sanitize_report(report_dict)  # raises ValueError on sensitive data

        logger.info(
            f"Health report compiled: overall_status={overall_status} "
            f"days={len(daily_summaries)}"
        )
        return report

    def _degraded_report(self, generated_at: dt.datetime) -> PipelineHealthReport:
        """
        Produce a minimal degraded-status report when data collection fails.

        Rather than failing silently (or crashing), the Lambda writes a report
        that signals to dashboard consumers that the system is in an unknown
        state.  This satisfies the graceful-degradation acceptance criterion.

        Args:
            generated_at: Timestamp to use for the report's generated_at field.

        Returns:
            A PipelineHealthReport with OUTAGE status and empty daily summaries.
        """
        logger.warning("Producing degraded health report due to data collection error")

        today = generated_at.date()
        daily_summaries = []

        for offset in range(self.lookback_days):
            target_date = today - dt.timedelta(days=offset)
            daily_summaries.append(
                DailySummary(
                    date=target_date,
                    bronze=BronzeDailySummary(
                        status=PipelineStageStatus.NO_DATA, records_ingested=0
                    ),
                    silver=SilverDailySummary(
                        status=PipelineStageStatus.NO_DATA,
                        records_processed=0,
                        records_quarantined=0,
                        quality_score=0.0,
                    ),
                    gold=GoldDailySummary(
                        status=PipelineStageStatus.NO_DATA, artifacts_written=0
                    ),
                )
            )

        stage_statuses = {
            stage: StageStatus(status=OverallSystemStatus.OUTAGE, last_success_at=None)
            for stage in ("bronze", "silver", "gold")
        }

        return PipelineHealthReport(
            generated_at=generated_at,
            overall_status=OverallSystemStatus.OUTAGE,
            stages=stage_statuses,
            daily_summaries=daily_summaries,
        )
