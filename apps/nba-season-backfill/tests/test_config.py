"""Tests for NBA season backfill application configuration."""

import os
from unittest.mock import patch

import pytest

from app.config import BackfillConfig


class TestBackfillConfig:
    """Test cases for BackfillConfig class."""

    def test_from_env_valid_config(self):
        """Test creating config from valid environment variables."""
        env_vars = {
            "AWS_REGION": "us-east-1",
            "S3_BUCKET_NAME": "test-bucket",
            "SEASON": "2024-25",
            "RATE_LIMIT_SECONDS": "10",
            "LOG_LEVEL": "DEBUG",
            "DRY_RUN": "true",
        }

        with patch.dict(os.environ, env_vars):
            config = BackfillConfig.from_env()

            assert config.aws_region == "us-east-1"
            assert config.s3_bucket_name == "test-bucket"
            assert config.season == "2024-25"
            assert config.rate_limit_seconds == 10
            assert config.log_level == "DEBUG"
            assert config.dry_run is True

    def test_from_env_missing_required(self):
        """Test error when required environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Required environment variable AWS_REGION"
            ):
                BackfillConfig.from_env()

    def test_from_env_defaults(self):
        """Test that optional environment variables use defaults."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "S3_BUCKET_NAME": "test-bucket",
            "SEASON": "2023-24",
        }

        with patch.dict(os.environ, env_vars):
            config = BackfillConfig.from_env()

            assert config.rate_limit_seconds == 5  # default
            assert config.log_level == "INFO"  # default
            assert config.dry_run is False  # default
            assert config.max_retries == 3  # default

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = BackfillConfig(
            aws_region="us-east-1", s3_bucket_name="test-bucket", season="2024-25"
        )

        # Should not raise any exceptions
        config.validate()

    def test_validate_invalid_rate_limit(self):
        """Test validation fails for invalid rate limit."""
        config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024-25",
            rate_limit_seconds=0,
        )

        with pytest.raises(ValueError, match="rate_limit_seconds must be at least 1"):
            config.validate()

    def test_validate_invalid_season_format(self):
        """Test validation fails for invalid season format."""
        config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024",  # Invalid format
        )

        with pytest.raises(ValueError, match="season must be in format YYYY-YY"):
            config.validate()

    def test_validate_invalid_season_years(self):
        """Test validation fails for inconsistent season years."""
        config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024-26",  # Should be 2024-25
        )

        with pytest.raises(ValueError, match="Invalid season format"):
            config.validate()

    def test_state_file_path_property(self):
        """Test state file path generation."""
        config = BackfillConfig(
            aws_region="us-east-1",
            s3_bucket_name="test-bucket",
            season="2024-25",
            state_file_prefix="custom-prefix",
        )

        assert config.state_file_path == "custom-prefix/checkpoint.json"

    def test_s3_data_prefix_property(self):
        """Test S3 data prefix generation."""
        config = BackfillConfig(
            aws_region="us-east-1", s3_bucket_name="test-bucket", season="2024-25"
        )

        assert config.s3_data_prefix == "historical-backfill/season=2024-25"
