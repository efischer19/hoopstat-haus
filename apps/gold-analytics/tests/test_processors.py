"""Tests for the processors module."""

from datetime import date

import pandas as pd
import pytest

from app.processors import GoldProcessor


class TestGoldProcessor:
    """Test cases for the GoldProcessor class."""

    def test_processor_initialization(self):
        """Test that processor can be initialized."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        assert processor.silver_bucket == "test-silver-bucket"
        assert processor.gold_bucket == "test-gold-bucket"

    def test_process_date_dry_run(self):
        """Test processing a date in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        result = processor.process_date(target_date, dry_run=True)
        assert result is True

    def test_load_silver_player_stats_dry_run(self):
        """Test loading player stats in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        stats = processor._load_silver_player_stats(target_date, dry_run=True)

        assert isinstance(stats, pd.DataFrame)
        assert len(stats) == 2
        assert "player_id" in stats.columns
        assert "points" in stats.columns

    def test_load_silver_team_stats_dry_run(self):
        """Test loading team stats in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        stats = processor._load_silver_team_stats(target_date, dry_run=True)

        assert isinstance(stats, pd.DataFrame)
        assert len(stats) == 2
        assert "team_id" in stats.columns
        assert "points" in stats.columns

    def test_calculate_player_analytics(self):
        """Test player analytics calculations."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Create test data
        player_stats = pd.DataFrame(
            {
                "player_id": ["player_1"],
                "points": [25],
                "rebounds": [8],
                "assists": [5],
                "steals": [2],
                "blocks": [1],
                "turnovers": [3],
                "field_goals_made": [10],
                "field_goals_attempted": [18],
                "free_throws_made": [3],
                "free_throws_attempted": [4],
                "minutes_played": [35],
            }
        )

        analytics = processor._calculate_player_analytics_enhanced(player_stats)

        # Check that new analytics columns were added
        assert "true_shooting_pct" in analytics.columns
        assert "player_efficiency_rating" in analytics.columns
        assert "usage_rate" in analytics.columns
        assert "points_per_shot" in analytics.columns
        assert "assists_per_turnover" in analytics.columns

        # Verify calculations
        expected_ts_pct = 25 / (2 * (18 + 0.44 * 4))
        assert abs(analytics["true_shooting_pct"].iloc[0] - expected_ts_pct) < 0.001

        # PER calculation: (25 + 8 + 5 + 2 + 1 - 3) / 35
        expected_per = (25 + 8 + 5 + 2 + 1 - 3) / 35
        assert (
            abs(analytics["player_efficiency_rating"].iloc[0] - expected_per) < 0.01
        )  # Allow for rounding

        # Points per shot: 25 / (18 + 4)
        expected_pps = 25 / (18 + 4)
        assert (
            abs(analytics["points_per_shot"].iloc[0] - expected_pps) < 0.01
        )  # Allow for rounding

        # Assists per turnover: 5 / 3
        expected_apt = 5 / 3
        assert abs(analytics["assists_per_turnover"].iloc[0] - expected_apt) < 0.01

    def test_process_season_aggregation_dry_run(self):
        """Test season aggregation processing in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        result = processor.process_season_aggregation("2023-24", dry_run=True)
        assert result is True

    def test_load_season_player_games_dry_run(self):
        """Test loading season player games in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Test loading all players
        games_data = processor._load_season_player_games("2023-24", dry_run=True)
        assert isinstance(games_data, dict)
        assert "player_1" in games_data
        assert len(games_data["player_1"]) == 2

        # Test loading specific player
        specific_data = processor._load_season_player_games(
            "2023-24", "player_1", dry_run=True
        )
        assert "player_1" in specific_data
        assert len(specific_data["player_1"]) == 2

    def test_season_aggregation_integration(self):
        """Test the integration with PlayerSeasonAggregator."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Verify the aggregator is properly initialized
        assert processor.season_aggregator is not None
        assert processor.season_aggregator.validation_mode == "lenient"

    def test_calculate_team_analytics(self):
        """Test team analytics calculations."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Create test data
        team_stats = pd.DataFrame(
            {
                "team_id": ["team_1"],
                "points": [110],
                "field_goals_made": [42],
                "field_goals_attempted": [85],
                "rebounds": [45],
                "turnovers": [12],
                "possessions": [98],
            }
        )

        analytics = processor._calculate_team_analytics(team_stats)

        # Check that new analytics columns were added
        assert "offensive_rating" in analytics.columns
        assert "defensive_rating" in analytics.columns
        assert "pace" in analytics.columns
        assert "true_shooting_pct" in analytics.columns

        # Verify calculations
        expected_ortg = (110 / 98) * 100
        assert abs(analytics["offensive_rating"].iloc[0] - expected_ortg) < 0.001

    def test_load_silver_data_not_implemented(self):
        """Test that non-dry-run data loading raises NotImplementedError."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)

        with pytest.raises(NotImplementedError):
            processor._load_silver_player_stats(target_date, dry_run=False)

        with pytest.raises(NotImplementedError):
            processor._load_silver_team_stats(target_date, dry_run=False)

    def test_process_date_normal_mode_fails(self):
        """Test that normal mode processing fails due to unimplemented data loading."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        result = processor.process_date(target_date, dry_run=False)
        assert result is False
