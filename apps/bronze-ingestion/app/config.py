"""Configuration management for bronze layer ingestion."""

from hoopstat_config import ConfigManager, config_field


class BronzeIngestionConfig(ConfigManager):
    """Configuration for bronze layer NBA data ingestion."""

    # AWS Configuration
    aws_region: str = config_field(
        default="us-east-1",
        env_var="AWS_REGION",
        description="AWS region for S3 operations",
    )

    bronze_bucket_name: str = config_field(
        env_var="BRONZE_BUCKET_NAME",
        description="S3 bucket name for bronze layer storage",
    )

    # Rate Limiting Configuration
    rate_limit_seconds: float = config_field(
        default=2.0,
        env_var="RATE_LIMIT_SECONDS",
        description="Minimum seconds between NBA API calls",
    )

    # Retry Configuration
    max_retries: int = config_field(
        default=3,
        env_var="MAX_RETRIES",
        description="Maximum number of retry attempts for API calls",
    )

    retry_base_delay: float = config_field(
        default=1.0,
        env_var="RETRY_BASE_DELAY",
        description="Base delay in seconds for exponential backoff",
    )

    retry_max_delay: float = config_field(
        default=60.0,
        env_var="RETRY_MAX_DELAY",
        description="Maximum delay in seconds for exponential backoff",
    )
