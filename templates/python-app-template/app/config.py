"""
Configuration management for the application.

This module handles loading configuration from environment variables
and .env files using pydantic-settings for type safety and validation.
"""

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    # Application Info
    app_name: str = Field(default="python-app-template", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )

    # API Settings
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")

    # Development Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    testing: bool = Field(default=False, description="Enable testing mode")

    # Database Settings (optional)
    database_url: str | None = Field(
        default=None, description="Database connection URL"
    )

    # AWS Configuration (optional)
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: str | None = Field(
        default=None, description="AWS access key ID"
    )
    aws_secret_access_key: str | None = Field(
        default=None, description="AWS secret access key"
    )
    s3_bucket_name: str | None = Field(default=None, description="S3 bucket name")

    # Security Settings
    secret_key: str | None = Field(default=None, description="Application secret key")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.testing or os.getenv("PYTEST_CURRENT_TEST") is not None


# Global settings instance
settings = Settings()