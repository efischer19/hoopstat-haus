"""Test configuration module."""

import pytest

from app.config import LambdaConfig


class TestLambdaConfig:
    """Test cases for LambdaConfig."""

    def test_from_environment_success(self, monkeypatch):
        """Test successful configuration from environment variables."""
        # Set required environment variables
        monkeypatch.setenv("SILVER_BUCKET", "test-silver-bucket")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold-bucket")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("MAX_WORKERS", "8")

        config = LambdaConfig.from_environment()

        assert config.silver_bucket == "test-silver-bucket"
        assert config.gold_bucket == "test-gold-bucket"
        assert config.aws_region == "us-west-2"
        assert config.max_workers == 8

    def test_from_environment_defaults(self, monkeypatch):
        """Test default values are used when optional env vars not set."""
        # Set only required environment variables
        monkeypatch.setenv("SILVER_BUCKET", "test-silver-bucket")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold-bucket")

        # Clear optional environment variables
        for key in ["AWS_REGION", "MAX_WORKERS", "CHUNK_SIZE"]:
            monkeypatch.delenv(key, raising=False)

        config = LambdaConfig.from_environment()

        assert config.silver_bucket == "test-silver-bucket"
        assert config.gold_bucket == "test-gold-bucket"
        assert config.aws_region == "us-east-1"  # default
        assert config.max_workers == 4  # default
        assert config.chunk_size == 10000  # default

    def test_from_environment_missing_silver_bucket(self, monkeypatch):
        """Test error when SILVER_BUCKET is missing."""
        monkeypatch.setenv("GOLD_BUCKET", "test-gold-bucket")
        monkeypatch.delenv("SILVER_BUCKET", raising=False)

        with pytest.raises(
            ValueError, match="SILVER_BUCKET environment variable is required"
        ):
            LambdaConfig.from_environment()

    def test_from_environment_missing_gold_bucket(self, monkeypatch):
        """Test error when GOLD_BUCKET is missing."""
        monkeypatch.setenv("SILVER_BUCKET", "test-silver-bucket")
        monkeypatch.delenv("GOLD_BUCKET", raising=False)

        with pytest.raises(
            ValueError, match="GOLD_BUCKET environment variable is required"
        ):
            LambdaConfig.from_environment()

    def test_configuration_values(self):
        """Test configuration with explicit values."""
        config = LambdaConfig(
            aws_region="eu-west-1",
            silver_bucket="my-silver",
            gold_bucket="my-gold",
            max_workers=6,
            chunk_size=5000,
            min_expected_players=10,
            max_null_percentage=0.05,
        )

        assert config.aws_region == "eu-west-1"
        assert config.silver_bucket == "my-silver"
        assert config.gold_bucket == "my-gold"
        assert config.max_workers == 6
        assert config.chunk_size == 5000
        assert config.min_expected_players == 10
        assert config.max_null_percentage == 0.05

    def test_season_validation_configuration_defaults(self, monkeypatch):
        """Test default values for season validation settings."""
        monkeypatch.setenv("SILVER_BUCKET", "test-silver-bucket")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold-bucket")

        config = LambdaConfig.from_environment()

        assert config.enable_season_totals_validation is True  # default
        assert config.season_totals_tolerance == 0.01  # default

    def test_season_validation_configuration_from_env(self, monkeypatch):
        """Test season validation settings from environment variables."""
        monkeypatch.setenv("SILVER_BUCKET", "test-silver-bucket")
        monkeypatch.setenv("GOLD_BUCKET", "test-gold-bucket")
        monkeypatch.setenv("ENABLE_SEASON_TOTALS_VALIDATION", "false")
        monkeypatch.setenv("SEASON_TOTALS_TOLERANCE", "0.05")

        config = LambdaConfig.from_environment()

        assert config.enable_season_totals_validation is False
        assert config.season_totals_tolerance == 0.05

    def test_configuration_with_season_validation_values(self):
        """Test configuration with explicit season validation values."""
        config = LambdaConfig(
            silver_bucket="my-silver",
            gold_bucket="my-gold",
            enable_season_totals_validation=False,
            season_totals_tolerance=0.02,
        )

        assert config.enable_season_totals_validation is False
        assert config.season_totals_tolerance == 0.02
