"""
Configuration management for NBA season backfill application.

Handles environment variables, command-line arguments, and configuration
validation per ADR-015 structured logging and application standards.
"""

import os

from pydantic import BaseModel, Field, validator


class BackfillConfig(BaseModel):
    """Configuration for NBA season backfill application."""

    # Season configuration
    target_season: str = Field(
        default="2024-25", description="NBA season to backfill (format: YYYY-YY)"
    )

    # NBA API configuration
    rate_limit_seconds: float = Field(
        default=5.0, description="Seconds to wait between NBA API requests"
    )

    # AWS S3 configuration
    s3_bucket: str = Field(
        default="hoopstat-haus-bronze", description="S3 bucket for Bronze layer storage"
    )
    s3_prefix: str = Field(
        default="historical-backfill", description="S3 prefix for backfill data"
    )
    aws_region: str = Field(
        default="us-east-1", description="AWS region for S3 operations"
    )

    # State management
    state_file_path: str = Field(
        default="s3://hoopstat-haus-bronze/backfill-state/checkpoint.json",
        description="Path to state/checkpoint file",
    )
    checkpoint_frequency: int = Field(
        default=10, description="Number of games between checkpoints"
    )

    # Processing configuration
    dry_run: bool = Field(
        default=False,
        description="Run in dry-run mode without making API calls or uploads",
    )
    resume_from_checkpoint: bool = Field(
        default=False, description="Resume from existing checkpoint"
    )
    max_retries: int = Field(
        default=3, description="Maximum retry attempts for transient failures"
    )

    # Data types to collect
    collect_box_scores: bool = Field(
        default=True, description="Collect traditional and advanced box scores"
    )
    collect_play_by_play: bool = Field(
        default=True, description="Collect play-by-play data"
    )
    collect_player_info: bool = Field(
        default=True, description="Collect player information"
    )

    @validator("target_season")
    def validate_season_format(cls, v):
        """Validate season format is YYYY-YY."""
        if not v or len(v) != 7 or v[4] != "-":
            raise ValueError("Season must be in format YYYY-YY (e.g., 2024-25)")

        try:
            year1 = int(v[:4])
            year2 = int(v[5:])
            if year2 != (year1 + 1) % 100:
                raise ValueError("Season years must be consecutive")
        except ValueError as e:
            raise ValueError("Season must be in format YYYY-YY with valid years") from e

        return v

    @validator("rate_limit_seconds")
    def validate_rate_limit(cls, v):
        """Ensure rate limit is reasonable for NBA API courtesy."""
        if v < 1.0:
            raise ValueError("Rate limit must be at least 1.0 seconds")
        return v

    @classmethod
    def from_env(cls) -> "BackfillConfig":
        """Create configuration from environment variables."""
        return cls(
            target_season=os.getenv("NBA_TARGET_SEASON", "2024-25"),
            rate_limit_seconds=float(os.getenv("NBA_RATE_LIMIT_SECONDS", "5.0")),
            s3_bucket=os.getenv("AWS_S3_BUCKET", "hoopstat-haus-bronze"),
            s3_prefix=os.getenv("AWS_S3_PREFIX", "historical-backfill"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            state_file_path=os.getenv(
                "STATE_FILE_PATH",
                "s3://hoopstat-haus-bronze/backfill-state/checkpoint.json",
            ),
            checkpoint_frequency=int(os.getenv("CHECKPOINT_FREQUENCY", "10")),
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            resume_from_checkpoint=os.getenv("RESUME_FROM_CHECKPOINT", "false").lower()
            == "true",
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            collect_box_scores=os.getenv("COLLECT_BOX_SCORES", "true").lower()
            == "true",
            collect_play_by_play=os.getenv("COLLECT_PLAY_BY_PLAY", "true").lower()
            == "true",
            collect_player_info=os.getenv("COLLECT_PLAYER_INFO", "true").lower()
            == "true",
        )
