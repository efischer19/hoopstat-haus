"""
Tests for NBA season backfill application configuration.
"""

import pytest
from pydantic import ValidationError

from app.config import BackfillConfig


class TestBackfillConfig:
    """Test configuration validation and parsing."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BackfillConfig()

        assert config.target_season == "2024-25"
        assert config.rate_limit_seconds == 5.0
        assert config.s3_bucket == "hoopstat-haus-bronze"
        assert config.dry_run is False
        assert config.collect_box_scores is True
        assert config.collect_play_by_play is True

    def test_season_validation_valid(self):
        """Test valid season format validation."""
        valid_seasons = ["2024-25", "2023-24", "1999-00"]

        for season in valid_seasons:
            config = BackfillConfig(target_season=season)
            assert config.target_season == season

    def test_season_validation_invalid(self):
        """Test invalid season format validation."""
        invalid_seasons = [
            "2024",
            "2024-2025",
            "24-25",
            "2024-26",  # Non-consecutive years
            "invalid",
        ]

        for season in invalid_seasons:
            with pytest.raises(ValidationError):
                BackfillConfig(target_season=season)

    def test_rate_limit_validation(self):
        """Test rate limit validation."""
        # Valid rate limits
        config = BackfillConfig(rate_limit_seconds=1.0)
        assert config.rate_limit_seconds == 1.0

        config = BackfillConfig(rate_limit_seconds=10.5)
        assert config.rate_limit_seconds == 10.5

        # Invalid rate limit
        with pytest.raises(ValidationError):
            BackfillConfig(rate_limit_seconds=0.5)

    def test_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("NBA_TARGET_SEASON", "2023-24")
        monkeypatch.setenv("NBA_RATE_LIMIT_SECONDS", "3.0")
        monkeypatch.setenv("AWS_S3_BUCKET", "test-bucket")
        monkeypatch.setenv("DRY_RUN", "true")
        monkeypatch.setenv("COLLECT_BOX_SCORES", "false")

        config = BackfillConfig.from_env()

        assert config.target_season == "2023-24"
        assert config.rate_limit_seconds == 3.0
        assert config.s3_bucket == "test-bucket"
        assert config.dry_run is True
        assert config.collect_box_scores is False

    def test_boolean_env_parsing(self, monkeypatch):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("yes", False),  # Only "true" should be True
            ("1", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("DRY_RUN", env_value)
            config = BackfillConfig.from_env()
            assert config.dry_run is expected
