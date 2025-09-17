"""
Configuration management for Gold Analytics application.

This module provides configuration management with environment variables
and default values following the project's development philosophy.
"""

import os
from dataclasses import dataclass
from typing import Any

from hoopstat_observability import get_logger

logger = get_logger(__name__)


@dataclass
class GoldAnalyticsConfig:
    """Configuration for Gold Analytics processing."""

    # S3 bucket configuration
    silver_bucket: str
    gold_bucket: str
    aws_region: str = "us-east-1"

    # Processing configuration
    max_concurrent_files: int = 10
    batch_size: int = 1000
    processing_timeout_minutes: int = 30

    # Retry configuration (following ADR-021)
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5
    retry_multiplier: float = 2.0
    retry_max_delay_seconds: int = 60

    # S3 Tables configuration
    catalog_type: str = "glue"
    iceberg_table_location_prefix: str = "s3a://"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.silver_bucket:
            raise ValueError("silver_bucket is required")
        if not self.gold_bucket:
            raise ValueError("gold_bucket is required")

        logger.info(
            f"Initialized GoldAnalyticsConfig with silver_bucket={self.silver_bucket}, "
            f"gold_bucket={self.gold_bucket}"
        )


def load_config() -> GoldAnalyticsConfig:
    """
    Load configuration from environment variables with sensible defaults.

    Returns:
        GoldAnalyticsConfig instance loaded from environment

    Raises:
        ValueError: If required configuration is missing
    """
    # Required configuration
    silver_bucket = os.getenv("SILVER_BUCKET")
    gold_bucket = os.getenv("GOLD_BUCKET")

    if not silver_bucket:
        raise ValueError("SILVER_BUCKET environment variable is required")
    if not gold_bucket:
        raise ValueError("GOLD_BUCKET environment variable is required")

    # Optional configuration with defaults
    config = GoldAnalyticsConfig(
        silver_bucket=silver_bucket,
        gold_bucket=gold_bucket,
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        max_concurrent_files=int(os.getenv("MAX_CONCURRENT_FILES", "10")),
        batch_size=int(os.getenv("BATCH_SIZE", "1000")),
        processing_timeout_minutes=int(os.getenv("PROCESSING_TIMEOUT_MINUTES", "30")),
        max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
        retry_delay_seconds=int(os.getenv("RETRY_DELAY_SECONDS", "5")),
        retry_multiplier=float(os.getenv("RETRY_MULTIPLIER", "2.0")),
        retry_max_delay_seconds=int(os.getenv("RETRY_MAX_DELAY_SECONDS", "60")),
        catalog_type=os.getenv("CATALOG_TYPE", "glue"),
        iceberg_table_location_prefix=os.getenv(
            "ICEBERG_TABLE_LOCATION_PREFIX", "s3a://"
        ),
    )

    return config


def get_configuration_dict() -> dict[str, Any]:
    """
    Get configuration as a dictionary for logging and debugging.

    Returns:
        Dictionary containing configuration values (sensitive values masked)
    """
    try:
        config = load_config()
        return {
            "silver_bucket": config.silver_bucket,
            "gold_bucket": config.gold_bucket,
            "aws_region": config.aws_region,
            "max_concurrent_files": config.max_concurrent_files,
            "batch_size": config.batch_size,
            "processing_timeout_minutes": config.processing_timeout_minutes,
            "max_retry_attempts": config.max_retry_attempts,
            "retry_delay_seconds": config.retry_delay_seconds,
            "retry_multiplier": config.retry_multiplier,
            "retry_max_delay_seconds": config.retry_max_delay_seconds,
            "catalog_type": config.catalog_type,
            "iceberg_table_location_prefix": config.iceberg_table_location_prefix,
        }
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return {"error": str(e)}
