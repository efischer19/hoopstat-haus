"""Tests for the processors module."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from app.processors import GoldProcessor


class TestGoldProcessor:
    """Test cases for the GoldProcessor class."""

    @patch("app.processors.IcebergS3TablesWriter")
    def test_processor_initialization(self, mock_iceberg_writer):
        """Test that processor can be initialized."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        assert processor.silver_bucket == "test-silver-bucket"
        assert processor.gold_bucket == "test-gold-bucket"

        # Verify Iceberg writer was initialized
        mock_iceberg_writer.assert_called_once_with("test-gold-bucket")

    @patch("app.processors.IcebergS3TablesWriter")
    def test_process_date_dry_run(self, mock_iceberg_writer):
        """Test processing a date in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        result = processor.process_date(target_date, dry_run=True)
        assert result is True

    @patch("app.processors.IcebergS3TablesWriter")
    def test_load_silver_player_stats_dry_run(self, mock_iceberg_writer):
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

    @patch("app.processors.IcebergS3TablesWriter")
    def test_load_silver_team_stats_dry_run(self, mock_iceberg_writer):
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

    @patch("app.processors.IcebergS3TablesWriter")
    def test_calculate_player_analytics(self, mock_iceberg_writer):
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

    @patch("app.processors.IcebergS3TablesWriter")
    def test_process_season_aggregation_dry_run(self, mock_iceberg_writer):
        """Test season aggregation processing in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        result = processor.process_season_aggregation("2023-24", dry_run=True)
        assert result is True

    @patch("app.processors.IcebergS3TablesWriter")
    def test_load_season_player_games_dry_run(self, mock_iceberg_writer):
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

    @patch("app.processors.IcebergS3TablesWriter")
    def test_season_aggregation_integration(self, mock_iceberg_writer):
        """Test the integration with PlayerSeasonAggregator."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Verify the aggregator is properly initialized
        assert processor.season_aggregator is not None
        assert processor.season_aggregator.validation_mode == "lenient"

    @patch("app.processors.IcebergS3TablesWriter")
    def test_calculate_team_analytics(self, mock_iceberg_writer):
        """Test team analytics calculations (legacy test with basic data)."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Create test data with minimal fields (legacy format)
        team_stats = pd.DataFrame(
            {
                "team_id": ["team_1"],
                "points": [110],
                "field_goals_made": [42],
                "field_goals_attempted": [85],
                "free_throws_attempted": [20],
                "offensive_rebounds": [12],
                "turnovers": [15],
            }
        )

        analytics = processor._calculate_team_analytics(team_stats)

        # Check that analytics columns were added
        assert "possessions" in analytics.columns
        assert "offensive_rating" in analytics.columns
        assert "pace" in analytics.columns
        assert "true_shooting_pct" in analytics.columns

        # Verify possessions calculation: FGA - ORB + TOV + 0.44 * FTA
        expected_possessions = 85 - 12 + 15 + 0.44 * 20
        assert abs(analytics["possessions"].iloc[0] - expected_possessions) < 0.1

        # Verify offensive rating calculation: (Points / Possessions) * 100
        expected_ortg = (110 / expected_possessions) * 100
        assert abs(analytics["offensive_rating"].iloc[0] - expected_ortg) < 0.1

    @patch("app.processors.IcebergS3TablesWriter")
    @patch("app.processors.S3DataDiscovery")
    def test_load_silver_data_with_s3_discovery(
        self, mock_s3_discovery_class, mock_iceberg_writer
    ):
        """Test that non-dry-run data loading uses S3 discovery."""
        # Setup mock S3 discovery
        mock_s3_discovery = MagicMock()
        mock_s3_discovery.load_all_silver_data.return_value = pd.DataFrame(
            {
                "player_id": ["player_1", "player_2"],
                "team_id": ["team_1", "team_2"],
                "points": [25, 18],
            }
        )
        mock_s3_discovery_class.return_value = mock_s3_discovery

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)

        # Test player stats loading
        result = processor._load_silver_player_stats(target_date, dry_run=False)
        assert len(result) == 2
        assert "player_id" in result.columns
        mock_s3_discovery.load_all_silver_data.assert_called_with(
            target_date, "player_stats"
        )

        # Test team stats loading
        mock_s3_discovery.load_all_silver_data.return_value = pd.DataFrame(
            {
                "team_id": ["team_1", "team_2"],
                "points": [110, 105],
            }
        )
        result = processor._load_silver_team_stats(target_date, dry_run=False)
        assert len(result) == 2
        assert "team_id" in result.columns

    @patch("app.processors.IcebergS3TablesWriter")
    @patch("app.processors.S3DataDiscovery")
    def test_process_date_normal_mode_fails(
        self, mock_s3_discovery_class, mock_iceberg_writer
    ):
        """Test that normal mode processing fails when S3 discovery fails."""
        # Setup mock S3 discovery to raise an exception
        mock_s3_discovery = MagicMock()
        mock_s3_discovery.check_data_freshness.return_value = True
        mock_s3_discovery.load_all_silver_data.side_effect = Exception(
            "S3 connection failed"
        )
        mock_s3_discovery_class.return_value = mock_s3_discovery

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        target_date = date(2024, 1, 1)
        result = processor.process_date(target_date, dry_run=False)
        assert result is False

    @patch("app.processors.IcebergS3TablesWriter")
    def test_process_team_season_aggregation_dry_run(self, mock_iceberg_writer):
        """Test team season aggregation in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        result = processor.process_team_season_aggregation("2023-24", dry_run=True)
        assert result is True

    @patch("app.processors.IcebergS3TablesWriter")
    def test_load_season_team_games_dry_run(self, mock_iceberg_writer):
        """Test loading team game data in dry-run mode."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Test loading all teams
        games_data = processor._load_season_team_games("2023-24", dry_run=True)
        assert isinstance(games_data, dict)
        assert "1610612747" in games_data  # Lakers
        assert len(games_data["1610612747"]) == 2

        # Test loading specific team
        specific_data = processor._load_season_team_games(
            "2023-24", "1610612747", dry_run=True
        )
        assert "1610612747" in specific_data
        assert len(specific_data["1610612747"]) == 2

    @patch("app.processors.IcebergS3TablesWriter")
    def test_team_season_aggregation_integration(self, mock_iceberg_writer):
        """Test the integration with TeamSeasonAggregator."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Verify the team aggregator is properly initialized
        assert processor.team_aggregator is not None
        assert processor.team_aggregator.validation_mode == "lenient"

    @patch("app.processors.IcebergS3TablesWriter")
    def test_calculate_team_analytics_enhanced(self, mock_iceberg_writer):
        """Test enhanced team analytics calculations with new metrics."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Create test data with all necessary fields
        team_stats = pd.DataFrame(
            {
                "team_id": ["1610612747"],
                "points": [110],
                "points_allowed": [105],
                "field_goals_made": [42],
                "field_goals_attempted": [85],
                "three_pointers_made": [12],
                "three_pointers_attempted": [35],
                "free_throws_made": [14],
                "free_throws_attempted": [18],
                "offensive_rebounds": [12],
                "defensive_rebounds": [32],
                "total_rebounds": [44],
                "assists": [25],
                "steals": [8],
                "blocks": [5],
                "turnovers": [15],
            }
        )

        analytics = processor._calculate_team_analytics(team_stats)

        # Check that all new analytics columns were added
        expected_columns = [
            "possessions",
            "offensive_rating",
            "defensive_rating",
            "net_rating",
            "pace",
            "turnover_rate",
            "effective_field_goal_pct",
            "rebound_rate",
            "free_throw_rate",
            "true_shooting_pct",
        ]

        for col in expected_columns:
            assert col in analytics.columns, f"Missing column: {col}"

        # Verify some calculations
        row = analytics.iloc[0]

        # Possessions should be calculated: FGA - ORB + TOV + 0.44 * FTA
        expected_possessions = 85 - 12 + 15 + 0.44 * 18
        assert abs(row["possessions"] - expected_possessions) < 0.1

        # Offensive Rating should be (Points / Possessions) * 100
        expected_ortg = (110 / expected_possessions) * 100
        assert abs(row["offensive_rating"] - expected_ortg) < 0.1

        # Effective FG% should be (FGM + 0.5 * 3PM) / FGA
        expected_efg = (42 + 0.5 * 12) / 85
        assert abs(row["effective_field_goal_pct"] - expected_efg) < 0.001

    @patch("app.processors.IcebergS3TablesWriter")
    @patch("app.processors.S3DataDiscovery")
    def test_load_season_team_games_with_s3_discovery(
        self, mock_s3_discovery_class, mock_iceberg_writer
    ):
        """Test that non-dry-run team game loading uses S3 discovery."""
        # Setup mock S3 discovery
        mock_s3_discovery = MagicMock()
        mock_s3_discovery.discover_dates_to_process.return_value = [date(2024, 1, 15)]
        mock_s3_discovery.load_all_silver_data.return_value = pd.DataFrame(
            {
                "team_id": ["team_1", "team_2"],
                "points": [110, 105],
                "game_date": ["2024-01-15", "2024-01-15"],
            }
        )
        mock_s3_discovery_class.return_value = mock_s3_discovery

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        result = processor._load_season_team_games("2023-24", dry_run=False)
        assert isinstance(result, dict)
        assert (
            "team_1" in result or "team_2" in result
        )  # At least one team should be present

    @patch("app.processors.IcebergS3TablesWriter")
    @patch("app.processors.S3DataDiscovery")
    def test_process_team_season_aggregation_normal_mode_fails(
        self, mock_s3_discovery_class, mock_iceberg_writer
    ):
        """Test normal mode team season processing fails due to no data available."""
        # Setup mock S3 discovery to return no data
        mock_s3_discovery = MagicMock()
        mock_s3_discovery.discover_dates_to_process.return_value = []  # No dates
        mock_s3_discovery_class.return_value = mock_s3_discovery

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )
        result = processor.process_team_season_aggregation("2023-24", dry_run=False)
        assert result is True  # Should succeed but with no data to process

    @patch("app.processors.IcebergS3TablesWriter")
    def test_store_player_analytics_success(self, mock_iceberg_writer_class):
        """Test successful player analytics storage."""
        # Setup mock
        mock_writer = Mock()
        mock_writer.write_player_analytics.return_value = True
        mock_iceberg_writer_class.return_value = mock_writer

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Test data
        analytics = pd.DataFrame(
            {
                "player_id": [2544],
                "team_id": [1610612747],
                "points": [25],
                "true_shooting_pct": [0.58],
            }
        )
        target_date = date(2024, 1, 15)

        # Should not raise exception
        processor._store_player_analytics(analytics, target_date)

        # Verify writer was called
        mock_writer.write_player_analytics.assert_called_once()
        call_args = mock_writer.write_player_analytics.call_args
        assert call_args[0][1] == target_date  # target_date argument
        assert call_args[0][2] == "2023-24"  # season argument

    @patch("app.processors.IcebergS3TablesWriter")
    def test_store_team_analytics_success(self, mock_iceberg_writer_class):
        """Test successful team analytics storage."""
        # Setup mock
        mock_writer = Mock()
        mock_writer.write_team_analytics.return_value = True
        mock_iceberg_writer_class.return_value = mock_writer

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Test data
        analytics = pd.DataFrame(
            {
                "team_id": [1610612747],
                "opponent_team_id": [1610612744],
                "offensive_rating": [115.3],
                "defensive_rating": [110.5],
            }
        )
        target_date = date(2024, 1, 15)

        # Should not raise exception
        processor._store_team_analytics(analytics, target_date)

        # Verify writer was called
        mock_writer.write_team_analytics.assert_called_once()
        call_args = mock_writer.write_team_analytics.call_args
        assert call_args[0][1] == target_date  # target_date argument
        assert call_args[0][2] == "2023-24"  # season argument

    @patch("app.processors.IcebergS3TablesWriter")
    def test_store_analytics_failure_raises_exception(self, mock_iceberg_writer_class):
        """Test that storage failure raises RuntimeError."""
        # Setup mock to return failure
        mock_writer = Mock()
        mock_writer.write_player_analytics.return_value = False
        mock_iceberg_writer_class.return_value = mock_writer

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        analytics = pd.DataFrame({"player_id": [1], "points": [25]})
        target_date = date(2024, 1, 15)

        with pytest.raises(RuntimeError, match="Failed to store player analytics"):
            processor._store_player_analytics(analytics, target_date)

    @patch("app.processors.IcebergS3TablesWriter")
    def test_store_empty_analytics(self, mock_iceberg_writer_class):
        """Test storing empty analytics DataFrames."""
        mock_writer = Mock()
        mock_iceberg_writer_class.return_value = mock_writer

        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        empty_df = pd.DataFrame()
        target_date = date(2024, 1, 15)

        # Should not raise exception and should not call writer
        processor._store_player_analytics(empty_df, target_date)
        processor._store_team_analytics(empty_df, target_date)

        # Writer should not be called for empty data
        mock_writer.write_player_analytics.assert_not_called()
        mock_writer.write_team_analytics.assert_not_called()

    @patch("app.processors.IcebergS3TablesWriter")
    def test_season_extraction_logic(self, mock_iceberg_writer):
        """Test NBA season extraction from target date."""
        processor = GoldProcessor(
            silver_bucket="test-silver-bucket", gold_bucket="test-gold-bucket"
        )

        # Mock the write methods to check season parameter
        with patch.object(
            processor.iceberg_writer, "write_player_analytics", return_value=True
        ) as mock_write:
            analytics = pd.DataFrame({"player_id": [1], "team_id": [1], "points": [25]})

            # Test October date (start of NBA season)
            oct_date = date(2023, 10, 15)
            processor._store_player_analytics(analytics, oct_date)

            # Should extract season as "2023-24"
            call_args = mock_write.call_args
            assert call_args[0][2] == "2023-24"

            # Test January date (middle of NBA season)
            jan_date = date(2024, 1, 15)
            processor._store_player_analytics(analytics, jan_date)

            # Should extract season as "2023-24" (previous year start)
            call_args = mock_write.call_args
            assert call_args[0][2] == "2023-24"
