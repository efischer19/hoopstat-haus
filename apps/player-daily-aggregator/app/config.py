"""
Configuration management for the player daily aggregator Lambda.

This module handles environment-based configuration.
"""

import os
from dataclasses import dataclass


@dataclass
class LambdaConfig:
    """Configuration for the player daily aggregator Lambda function."""

    # AWS Configuration
    aws_region: str = "us-east-1"

    # S3 Configuration
    silver_bucket: str = ""
    gold_bucket: str = ""

    # Processing Configuration
    max_workers: int = 4
    chunk_size: int = 10000

    # Validation Configuration
    min_expected_players: int = 1
    max_null_percentage: float = 0.1  # 10% max null values allowed
    enable_season_totals_validation: bool = True
    season_totals_tolerance: float = 0.01  # 1% tolerance for discrepancies

    @classmethod
    def from_environment(cls) -> "LambdaConfig":
        """
        Create configuration from environment variables.

        Returns:
            LambdaConfig instance populated from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        # Required environment variables
        silver_bucket = os.getenv("SILVER_BUCKET")
        gold_bucket = os.getenv("GOLD_BUCKET")

        if not silver_bucket:
            raise ValueError("SILVER_BUCKET environment variable is required")
        if not gold_bucket:
            raise ValueError("GOLD_BUCKET environment variable is required")

        return cls(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            silver_bucket=silver_bucket,
            gold_bucket=gold_bucket,
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "10000")),
            min_expected_players=int(os.getenv("MIN_EXPECTED_PLAYERS", "1")),
            max_null_percentage=float(os.getenv("MAX_NULL_PERCENTAGE", "0.1")),
            enable_season_totals_validation=os.getenv(
                "ENABLE_SEASON_TOTALS_VALIDATION", "true"
            ).lower()
            == "true",
            season_totals_tolerance=float(os.getenv("SEASON_TOTALS_TOLERANCE", "0.01")),
        )
