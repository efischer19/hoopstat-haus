"""
Pipeline health data models for the static health dashboard.

These models define the schema for the pipeline_health.json artifact
consumed by the health dashboard UI. They capture a rolling 7-day window
of daily pipeline execution summaries across Medallion layers (Bronze,
Silver, Gold), along with overall system status and data quality metrics.

Security constraints (per ADR-040): No error messages, stack traces,
internal identifiers, durations, or start times are included.

These models are intentionally kept in a separate module so they can be
imported without triggering the heavy dependencies (pandas, fuzzywuzzy)
pulled in by the main hoopstat_data package __init__.py.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class PipelineStageStatus(StrEnum):
    """Status of a single pipeline stage execution."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NO_DATA = "no_data"


class OverallSystemStatus(StrEnum):
    """Overall system health status indicator."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OUTAGE = "outage"


class StageStatus(BaseModel):
    """Current status of a single Medallion pipeline stage."""

    status: OverallSystemStatus = Field(
        ..., description="Current status of this pipeline stage"
    )
    last_success_at: dt.datetime | None = Field(
        None, description="ISO 8601 UTC timestamp of last successful execution"
    )

    @field_validator("last_success_at")
    @classmethod
    def validate_utc_timestamp(cls, v):
        """Validate that the timestamp is timezone-aware (UTC)."""
        if v is not None and v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class BronzeDailySummary(BaseModel):
    """Daily summary for the Bronze (ingestion) pipeline stage."""

    status: PipelineStageStatus = Field(
        ..., description="Execution status of the Bronze stage for this day"
    )
    records_ingested: int = Field(
        ge=0, description="Number of records ingested from source systems"
    )


class SilverDailySummary(BaseModel):
    """Daily summary for the Silver (cleaning/validation) pipeline stage."""

    status: PipelineStageStatus = Field(
        ..., description="Execution status of the Silver stage for this day"
    )
    records_processed: int = Field(
        ge=0, description="Number of records successfully processed"
    )
    records_quarantined: int = Field(
        ge=0, description="Number of records sent to quarantine"
    )
    quality_score: float = Field(
        ge=0.0, le=1.0, description="Data quality score (0.0 = worst, 1.0 = best)"
    )


class GoldDailySummary(BaseModel):
    """Daily summary for the Gold (analytics) pipeline stage."""

    status: PipelineStageStatus = Field(
        ..., description="Execution status of the Gold stage for this day"
    )
    artifacts_written: int = Field(
        ge=0, description="Number of Gold layer artifacts written"
    )


class DailySummary(BaseModel):
    """Aggregated daily pipeline summary across all Medallion layers."""

    date: dt.date = Field(..., description="Date of this summary (YYYY-MM-DD)")
    bronze: BronzeDailySummary = Field(
        ..., description="Bronze stage summary for this day"
    )
    silver: SilverDailySummary = Field(
        ..., description="Silver stage summary for this day"
    )
    gold: GoldDailySummary = Field(..., description="Gold stage summary for this day")


class PipelineHealthReport(BaseModel):
    """
    Top-level pipeline health report consumed by the health dashboard.

    Contains a rolling 7-day window of daily pipeline execution summaries
    across all three Medallion layers, along with an overall system status
    indicator and per-stage status details.
    """

    schema_version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="SemVer schema version for backward-compatible evolution",
    )
    generated_at: dt.datetime = Field(
        ..., description="ISO 8601 UTC timestamp when this report was generated"
    )
    overall_status: OverallSystemStatus = Field(
        ..., description="Overall system health status"
    )
    stages: dict[str, StageStatus] = Field(
        ..., description="Per-stage status for each Medallion layer"
    )
    daily_summaries: list[DailySummary] = Field(
        default_factory=list,
        max_length=7,
        description="Rolling 7-day window of daily summaries, most-recent first",
    )

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at_utc(cls, v):
        """Validate that generated_at is timezone-aware (UTC)."""
        if v.tzinfo is None:
            raise ValueError("generated_at must be timezone-aware (UTC)")
        return v

    @field_validator("stages")
    @classmethod
    def validate_stage_keys(cls, v):
        """Validate that stages contains only valid Medallion layer keys."""
        valid_keys = {"bronze", "silver", "gold"}
        invalid_keys = set(v.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(
                f"Invalid stage keys: {invalid_keys}. Valid keys are: {valid_keys}"
            )
        return v

    @model_validator(mode="after")
    def validate_daily_summaries_order(self):
        """Validate that daily_summaries are ordered most-recent first."""
        dates = [s.date for s in self.daily_summaries]
        if dates != sorted(dates, reverse=True):
            raise ValueError("daily_summaries must be ordered most-recent first")
        return self
