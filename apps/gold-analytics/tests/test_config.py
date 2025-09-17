"""Tests for the config module."""

import os
from unittest.mock import patch

import pytest

from app.config import GoldAnalyticsConfig, load_config


class TestGoldAnalyticsConfig:
    """Test cases for the GoldAnalyticsConfig class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = GoldAnalyticsConfig(
            silver_bucket="test-silver",
            gold_bucket="test-gold"
        )
        
        assert config.silver_bucket == "test-silver"
        assert config.gold_bucket == "test-gold"
        assert config.aws_region == "us-east-1"  # default
        assert config.max_retry_attempts == 3  # default

    def test_config_validation_missing_silver_bucket(self):
        """Test config validation with missing silver bucket."""
        with pytest.raises(ValueError, match="silver_bucket is required"):
            GoldAnalyticsConfig(silver_bucket="", gold_bucket="test-gold")

    def test_config_validation_missing_gold_bucket(self):
        """Test config validation with missing gold bucket."""
        with pytest.raises(ValueError, match="gold_bucket is required"):
            GoldAnalyticsConfig(silver_bucket="test-silver", gold_bucket="")


class TestLoadConfig:
    """Test cases for the load_config function."""

    @patch.dict(os.environ, {
        "SILVER_BUCKET": "env-silver",
        "GOLD_BUCKET": "env-gold",
        "AWS_REGION": "us-west-2",
        "MAX_RETRY_ATTEMPTS": "5"
    })
    def test_load_config_from_environment(self):
        """Test loading config from environment variables."""
        config = load_config()
        
        assert config.silver_bucket == "env-silver"
        assert config.gold_bucket == "env-gold"
        assert config.aws_region == "us-west-2"
        assert config.max_retry_attempts == 5

    def test_load_config_missing_silver_bucket(self):
        """Test load_config with missing SILVER_BUCKET."""
        with pytest.raises(ValueError, match="SILVER_BUCKET environment variable is required"):
            load_config()

    @patch.dict(os.environ, {"SILVER_BUCKET": "test-silver"}, clear=True)
    def test_load_config_missing_gold_bucket(self):
        """Test load_config with missing GOLD_BUCKET."""
        with pytest.raises(ValueError, match="GOLD_BUCKET environment variable is required"):
            load_config()

    @patch.dict(os.environ, {
        "SILVER_BUCKET": "test-silver",
        "GOLD_BUCKET": "test-gold"
    }, clear=True)
    def test_load_config_with_defaults(self):
        """Test load_config with default values."""
        config = load_config()
        
        assert config.silver_bucket == "test-silver"
        assert config.gold_bucket == "test-gold"
        assert config.aws_region == "us-east-1"  # default
        assert config.max_concurrent_files == 10  # default
        assert config.batch_size == 1000  # default