"""Configuration management for NBA season backfill application."""

import os
from dataclasses import dataclass


@dataclass
class BackfillConfig:
    """Configuration for NBA season backfill application."""

    # Required settings
    aws_region: str
    s3_bucket_name: str
    season: str

    # Optional settings with defaults
    rate_limit_seconds: int = 5
    state_file_prefix: str = "backfill-state"
    log_level: str = "INFO"
    dry_run: bool = False
    max_retries: int = 3
    retry_delay: int = 10
    concurrent_uploads: int = 3
    checkpoint_frequency: int = 10  # Save state every N games

    @classmethod
    def from_env(cls) -> "BackfillConfig":
        """Create configuration from environment variables."""
        # Required environment variables
        required_vars = {
            "AWS_REGION": "aws_region",
            "S3_BUCKET_NAME": "s3_bucket_name",
            "SEASON": "season",
        }

        config_kwargs = {}

        # Check required variables
        for env_var, config_key in required_vars.items():
            value = os.getenv(env_var)
            if not value:
                raise ValueError(f"Required environment variable {env_var} is not set")
            config_kwargs[config_key] = value

        # Optional variables with type conversion
        config_kwargs["rate_limit_seconds"] = int(os.getenv("RATE_LIMIT_SECONDS", "5"))
        config_kwargs["state_file_prefix"] = os.getenv(
            "STATE_FILE_PREFIX", "backfill-state"
        )
        config_kwargs["log_level"] = os.getenv("LOG_LEVEL", "INFO")
        config_kwargs["dry_run"] = os.getenv("DRY_RUN", "false").lower() == "true"
        config_kwargs["max_retries"] = int(os.getenv("MAX_RETRIES", "3"))
        config_kwargs["retry_delay"] = int(os.getenv("RETRY_DELAY", "10"))
        config_kwargs["concurrent_uploads"] = int(os.getenv("CONCURRENT_UPLOADS", "3"))
        config_kwargs["checkpoint_frequency"] = int(
            os.getenv("CHECKPOINT_FREQUENCY", "10")
        )

        return cls(**config_kwargs)

    def validate(self) -> None:
        """Validate configuration values."""
        if self.rate_limit_seconds < 1:
            raise ValueError("rate_limit_seconds must be at least 1")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")

        if self.concurrent_uploads < 1:
            raise ValueError("concurrent_uploads must be at least 1")

        if self.checkpoint_frequency < 1:
            raise ValueError("checkpoint_frequency must be at least 1")

        # Validate season format (e.g., "2024-25")
        if not self.season.count("-") == 1:
            raise ValueError("season must be in format YYYY-YY (e.g., 2024-25)")

        try:
            year_parts = self.season.split("-")
            start_year = int(year_parts[0])
            end_year_suffix = int(year_parts[1])

            # Basic validation that end year follows start year
            expected_end_year = start_year + 1
            if end_year_suffix != expected_end_year % 100:
                raise ValueError(f"Invalid season format: {self.season}")

        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"season must contain valid year numbers: {self.season}"
                ) from None
            raise

    @property
    def state_file_path(self) -> str:
        """Get the S3 path for the state file."""
        return f"{self.state_file_prefix}/checkpoint.json"

    @property
    def s3_data_prefix(self) -> str:
        """Get the S3 prefix for storing data."""
        return f"historical-backfill/season={self.season}"
