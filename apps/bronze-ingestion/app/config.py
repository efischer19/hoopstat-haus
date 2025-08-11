"""
Configuration for bronze-ingestion application.
"""

from hoopstat_config import ConfigManager, config_field


class BronzeIngestionConfig(ConfigManager):
    """Configuration for bronze ingestion application."""

    # AWS Configuration
    aws_region: str = config_field(
        default="us-east-1",
        env_var="AWS_REGION",
        description="AWS region for S3 bucket",
    )

    bronze_bucket: str = config_field(
        default="test-bronze-bucket",
        env_var="BRONZE_BUCKET",
        description="S3 bucket name for bronze layer storage",
    )

    # Rate limiting configuration
    api_requests_per_minute: int = config_field(
        default=30,
        env_var="API_REQUESTS_PER_MINUTE",
        description="Maximum API requests per minute",
    )

    # Retry configuration
    max_retries: int = config_field(
        default=3,
        env_var="MAX_RETRIES",
        description="Maximum number of retries for failed operations",
    )
