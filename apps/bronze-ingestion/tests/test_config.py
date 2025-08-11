"""Tests for the BronzeIngestionConfig."""

import os
import tempfile
from unittest.mock import patch

import pytest

from app.config import BronzeIngestionConfig


class TestBronzeIngestionConfig:
    """Test bronze ingestion configuration management."""

    def test_config_with_required_fields(self):
        """Test configuration loads with required environment variables."""
        with patch.dict(os.environ, {"BRONZE_BUCKET_NAME": "test-bucket"}):
            config = BronzeIngestionConfig.load()
            assert config.bronze_bucket_name == "test-bucket"
            assert config.aws_region == "us-east-1"  # default
            assert config.rate_limit_seconds == 2.0  # default

    def test_config_with_all_environment_variables(self):
        """Test configuration with all environment variables set."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "BRONZE_BUCKET_NAME": "custom-bucket",
            "RATE_LIMIT_SECONDS": "1.5",
            "MAX_RETRIES": "5",
            "RETRY_BASE_DELAY": "2.0",
            "RETRY_MAX_DELAY": "120.0",
        }

        with patch.dict(os.environ, env_vars):
            config = BronzeIngestionConfig.load()

            assert config.aws_region == "us-west-2"
            assert config.bronze_bucket_name == "custom-bucket"
            assert config.rate_limit_seconds == 1.5
            assert config.max_retries == 5
            assert config.retry_base_delay == 2.0
            assert config.retry_max_delay == 120.0

    def test_config_missing_required_field(self):
        """Test configuration fails when required field is missing."""
        # Clear any existing environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                (ValueError, Exception)
            ):  # hoopstat-config should raise validation error
                BronzeIngestionConfig.load()

    def test_config_from_file(self):
        """Test configuration loading from file."""
        config_data = {
            "bronze_bucket_name": "file-bucket",
            "aws_region": "eu-west-1",
            "rate_limit_seconds": 3.0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            config_file = f.name

        try:
            config = BronzeIngestionConfig.load(config_file=config_file)
            assert config.bronze_bucket_name == "file-bucket"
            assert config.aws_region == "eu-west-1"
            assert config.rate_limit_seconds == 3.0
        finally:
            os.unlink(config_file)

    def test_config_precedence(self):
        """Test that environment variables override file values."""
        # Create config file
        config_data = {"bronze_bucket_name": "file-bucket", "aws_region": "eu-west-1"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            config_file = f.name

        try:
            # Set environment variable to override file
            with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}):
                config = BronzeIngestionConfig.load(config_file=config_file)

                assert config.bronze_bucket_name == "file-bucket"  # from file
                assert config.aws_region == "us-east-1"  # from environment
        finally:
            os.unlink(config_file)
