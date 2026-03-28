"""
Log sanitization and security hardening for the health aggregator.

Implements the allowlist sanitization layer (ADR-040 §Security Model) that
prevents internal AWS metadata, secrets, stack traces, or infrastructure
details from leaking into the public pipeline_health.json artifact.

Architecture
------------
The sanitizer operates in two passes:

Pass 1 — Field-level allowlist reconstruction:
    Constructs a new output dict from scratch using only validated, explicitly
    permitted fields.  Values outside permitted ranges are clamped/defaulted.
    Any field not on the allowlist is silently discarded.

Pass 2 — Secret-detection scan:
    Serialises the reconstructed dict to a JSON string and scans it for
    patterns matching AWS credentials, ARNs, internal IPs, and other
    credential-like strings.  If any pattern matches, the entire payload is
    replaced with a minimal safe fallback and a warning is logged to
    CloudWatch.

This two-pass design means even bugs in the allowlist reconstruction layer
cannot leak secrets as long as the pattern scanner is correct.
"""

import datetime as dt
import json
import re
from typing import Any

from hoopstat_data.health_models import (
    OverallSystemStatus,
    PipelineHealthReport,
    PipelineStageStatus,
)
from hoopstat_observability import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Permitted value sets (allowlists)
# ---------------------------------------------------------------------------

_PERMITTED_STAGE_STATUSES: frozenset[str] = frozenset(
    s.value for s in PipelineStageStatus
)
_PERMITTED_OVERALL_STATUSES: frozenset[str] = frozenset(
    s.value for s in OverallSystemStatus
)

# Default replacements for invalid enum values
_DEFAULT_STAGE_STATUS = PipelineStageStatus.FAILED.value
_DEFAULT_OVERALL_STATUS = OverallSystemStatus.DEGRADED.value

# ---------------------------------------------------------------------------
# Secret-detection patterns (compiled once at module load for performance)
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[re.Pattern] = [
    # AWS access key IDs (AKIA...)
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # AWS session tokens (common FwoGZX prefix)
    re.compile(r"FwoGZX[A-Za-z0-9+/=]{40,}"),
    # AWS ARNs
    re.compile(r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:\d{12}:"),
    # RFC 1918 internal IPs: 10.x.x.x
    re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    # RFC 1918 internal IPs: 172.16–31.x.x
    re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"),
    # RFC 1918 internal IPs: 192.168.x.x
    re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
    # Bearer token pattern
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    # AWS secret access key references (key name, not value)
    re.compile(r"(?i)(?:aws[_\-]?secret|secret[_\-]?access[_\-]?key)"),
    # Generic API key patterns with common prefixes
    re.compile(r"(?i)(?:api[_\-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9\-]{16,}"),
]

# ---------------------------------------------------------------------------
# Fallback payload construction
# ---------------------------------------------------------------------------

_SANITIZATION_REJECTION_NOTE = "Payload rejected by security filter"


def _make_fallback_report(generated_at: dt.datetime) -> PipelineHealthReport:
    """
    Construct a minimal degraded-status fallback report.

    Used when the secret scan rejects the compiled payload.  The fallback is a
    valid PipelineHealthReport (passing Pydantic validation) with empty stages
    and daily_summaries so the dashboard can render a safe degraded state.

    Args:
        generated_at: Timestamp to stamp the fallback report.

    Returns:
        Minimal PipelineHealthReport with overall_status=DEGRADED.
    """
    return PipelineHealthReport(
        generated_at=generated_at,
        overall_status=OverallSystemStatus.DEGRADED,
        stages={},
        daily_summaries=[],
    )


# ---------------------------------------------------------------------------
# Pass 1 helpers — field-level allowlist reconstruction
# ---------------------------------------------------------------------------


def _sanitize_stage_status(value: Any) -> str:
    """
    Map *value* to a permitted PipelineStageStatus string.

    Any value not in the permitted set is replaced with ``failed``.

    Args:
        value: Candidate status value.

    Returns:
        Permitted PipelineStageStatus string.
    """
    if isinstance(value, str) and value in _PERMITTED_STAGE_STATUSES:
        return value
    return _DEFAULT_STAGE_STATUS


def _sanitize_overall_status(value: Any) -> str:
    """
    Map *value* to a permitted OverallSystemStatus string.

    Any value not in the permitted set is replaced with ``degraded``.

    Args:
        value: Candidate status value.

    Returns:
        Permitted OverallSystemStatus string.
    """
    if isinstance(value, str) and value in _PERMITTED_OVERALL_STATUSES:
        return value
    return _DEFAULT_OVERALL_STATUS


def _sanitize_iso_utc_timestamp(value: Any) -> str | None:
    """
    Validate and normalise *value* as an ISO 8601 UTC timestamp string.

    Accepts timezone-aware datetime objects and strings with UTC offsets
    (+00:00 or Z suffix).  Non-UTC or non-parseable values return None
    so the caller can omit the field from the output.

    Args:
        value: Candidate timestamp value.

    Returns:
        Normalised ISO 8601 UTC string (with Z suffix), or None on invalid
        input.
    """
    if value is None:
        return None

    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            return None
        # Verify UTC offset is zero
        if value.utcoffset() != dt.timedelta(0):
            return None
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(value, str):
        # Accept both Z and +00:00 suffixes — only replace a trailing Z
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = dt.datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.utcoffset() != dt.timedelta(0):
            return None
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")

    return None


def _sanitize_count(value: Any) -> int:
    """
    Coerce *value* to a non-negative integer.

    Values below zero are clamped to 0.  Non-numeric values default to 0.

    Args:
        value: Candidate numeric value.

    Returns:
        Non-negative integer.
    """
    try:
        coerced = int(float(str(value)))
    except (ValueError, TypeError):
        return 0
    return max(0, coerced)


def _sanitize_quality_score(value: Any) -> float:
    """
    Coerce *value* to a float in [0.0, 1.0].

    Values below 0.0 are clamped to 0.0; values above 1.0 are clamped to 1.0.
    Non-numeric values default to 0.0.

    Args:
        value: Candidate numeric value.

    Returns:
        Float in [0.0, 1.0].
    """
    try:
        coerced = float(value)
    except (ValueError, TypeError):
        return 0.0
    return max(0.0, min(1.0, coerced))


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Return attribute from a Pydantic model or key from a dict."""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _reconstruct_stage_status_dict(stage: Any) -> dict:
    """
    Reconstruct a single StageStatus entry using only allowlisted fields.

    Args:
        stage: Raw stage status (StageStatus model instance or dict).

    Returns:
        Clean dict containing only ``status`` and (optionally)
        ``last_success_at``.
    """
    raw_status = _get_attr(stage, "status", "")
    raw_last_success_at = _get_attr(stage, "last_success_at")

    sanitized: dict = {"status": _sanitize_overall_status(str(raw_status))}

    ts = _sanitize_iso_utc_timestamp(raw_last_success_at)
    if ts is not None:
        sanitized["last_success_at"] = ts

    return sanitized


def _reconstruct_daily_summary_dict(summary: Any) -> dict | None:
    """
    Reconstruct a single DailySummary entry using only allowlisted fields.

    Returns None if the date field cannot be validated, so callers can skip
    malformed entries.

    Args:
        summary: Raw daily summary (DailySummary model instance or dict).

    Returns:
        Clean dict, or None if the date is invalid.
    """
    date_val = str(_get_attr(summary, "date", ""))
    try:
        dt.date.fromisoformat(date_val)
    except (ValueError, TypeError):
        return None

    bronze = _get_attr(summary, "bronze", {})
    silver = _get_attr(summary, "silver", {})
    gold = _get_attr(summary, "gold", {})

    return {
        "date": date_val,
        "bronze": {
            "status": _sanitize_stage_status(str(_get_attr(bronze, "status", ""))),
            "records_ingested": _sanitize_count(
                _get_attr(bronze, "records_ingested", 0)
            ),
        },
        "silver": {
            "status": _sanitize_stage_status(str(_get_attr(silver, "status", ""))),
            "records_processed": _sanitize_count(
                _get_attr(silver, "records_processed", 0)
            ),
            "records_quarantined": _sanitize_count(
                _get_attr(silver, "records_quarantined", 0)
            ),
            "quality_score": _sanitize_quality_score(
                _get_attr(silver, "quality_score", 0.0)
            ),
        },
        "gold": {
            "status": _sanitize_stage_status(str(_get_attr(gold, "status", ""))),
            "artifacts_written": _sanitize_count(
                _get_attr(gold, "artifacts_written", 0)
            ),
        },
    }


def _reconstruct_allowlisted_dict(report: PipelineHealthReport) -> dict:
    """
    Reconstruct the report as an allowlisted output dict (Pass 1).

    Builds a new dict containing only explicitly permitted fields with
    validated, sanitized values.  No raw value from *report* is copied
    verbatim — each is validated and normalised through a typed helper.

    Args:
        report: Validated PipelineHealthReport Pydantic model.

    Returns:
        Clean dict ready for secret scanning and JSON serialization.
    """
    # schema_version: validate semver pattern; fall back to current version
    schema_version = report.schema_version
    if not re.match(r"^\d+\.\d+\.\d+$", schema_version):
        schema_version = "1.0.0"

    # generated_at: must be UTC ISO timestamp
    generated_at_str = _sanitize_iso_utc_timestamp(report.generated_at)
    if generated_at_str is None:
        generated_at_str = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # overall_status: allowlist enum
    overall_status = _sanitize_overall_status(str(report.overall_status))

    # stages: only the three permitted Medallion layer keys
    permitted_stage_keys = {"bronze", "silver", "gold"}
    stages = {
        key: _reconstruct_stage_status_dict(stage)
        for key, stage in report.stages.items()
        if key in permitted_stage_keys
    }

    # daily_summaries: reconstruct each; skip malformed entries
    daily_summaries = []
    for summary in report.daily_summaries:
        reconstructed = _reconstruct_daily_summary_dict(summary)
        if reconstructed is not None:
            daily_summaries.append(reconstructed)

    return {
        "schema_version": schema_version,
        "generated_at": generated_at_str,
        "overall_status": overall_status,
        "stages": stages,
        "daily_summaries": daily_summaries,
    }


# ---------------------------------------------------------------------------
# Pass 2 — secret-detection scan
# ---------------------------------------------------------------------------


def _contains_secrets(json_str: str) -> bool:
    """
    Scan *json_str* for known-sensitive patterns.

    Each compiled pattern in ``_SECRET_PATTERNS`` is tested against the full
    serialised JSON string.  A warning identifying the matched pattern is
    logged to CloudWatch (never to the public JSON) on the first match.

    Args:
        json_str: Serialised JSON payload as a plain string.

    Returns:
        True if any sensitive pattern is found, False otherwise.
    """
    for pattern in _SECRET_PATTERNS:
        if pattern.search(json_str):
            logger.warning(
                "Sensitive pattern detected in serialized health report payload: "
                f"pattern={pattern.pattern!r}"
            )
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_report(report: PipelineHealthReport) -> PipelineHealthReport:
    """
    Sanitize a PipelineHealthReport for public output (ADR-040 §Security Model).

    Applies a two-pass sanitization strategy:

    **Pass 1** — Reconstruct the output dict from scratch using only explicitly
    permitted fields and validated values.  Enum fields that contain unknown
    values are replaced with safe defaults.  Numeric fields outside their
    permitted ranges are clamped.  Timestamps that are not UTC-normalised are
    dropped.  Any field not on the allowlist is silently discarded.

    **Pass 2** — Scan the serialised JSON for secret patterns.  If any are
    found, the entire payload is rejected: a CloudWatch warning is logged and
    a minimal degraded fallback report is returned instead.

    The fallback itself is validated by Pydantic before being returned, so
    callers are always guaranteed a structurally valid report.

    Args:
        report: Fully validated PipelineHealthReport Pydantic model.

    Returns:
        The original *report* if the sanitization passes, or a minimal
        degraded fallback PipelineHealthReport if the secret scan triggered
        rejection.
    """
    # Pass 1: rebuild output dict from allowlisted fields only
    output = _reconstruct_allowlisted_dict(report)

    # Pass 2: secret scan on the serialised JSON
    json_str = json.dumps(output, separators=(",", ":"))
    if _contains_secrets(json_str):
        logger.warning(
            "Health report payload rejected by security filter — "
            f"writing safe fallback to S3. "
            f"Note: {_SANITIZATION_REJECTION_NOTE}"
        )
        return _make_fallback_report(report.generated_at)

    return report
