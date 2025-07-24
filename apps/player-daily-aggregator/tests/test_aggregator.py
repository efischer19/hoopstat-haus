"""Test aggregator module."""

import pandas as pd
import pytest
from unittest.mock import Mock, patch

from app.aggregator import PlayerStatsAggregator
from app.config import LambdaConfig


class TestPlayerStatsAggregator:
    """Test cases for PlayerStatsAggregator."""

    def test_parse_key_metadata_success(self):
        """Test successful parsing of season and date from S3 key."""
        aggregator = self._create_aggregator()
        
        key = "silver/player_games/season=2023-24/date=2024-01-15/player_stats.parquet"
        season, date = aggregator._parse_key_metadata(key)
        
        assert season == "2023-24"
        assert date == "2024-01-15"

    def test_parse_key_metadata_missing_season(self):
        """Test error when season is missing from key."""
        aggregator = self._create_aggregator()
        
        key = "silver/player_games/date=2024-01-15/player_stats.parquet"
        
        with pytest.raises(ValueError, match="Could not parse season and date"):
            aggregator._parse_key_metadata(key)

    def test_parse_key_metadata_missing_date(self):
        """Test error when date is missing from key."""
        aggregator = self._create_aggregator()
        
        key = "silver/player_games/season=2023-24/player_stats.parquet"
        
        with pytest.raises(ValueError, match="Could not parse season and date"):
            aggregator._parse_key_metadata(key)

    def test_create_daily_aggregations(self):
        """Test creation of daily aggregations."""
        aggregator = self._create_aggregator()
        
        # Create test input data
        input_df = pd.DataFrame({
            'player_id': ['player1', 'player1', 'player2'],
            'points': [25, 18, 12],
            'rebounds': [8, 6, 4],
            'assists': [5, 3, 2],
            'field_goals_made': [10, 7, 5],
            'field_goals_attempted': [20, 15, 12],
            'three_pointers_made': [3, 2, 1],
            'three_pointers_attempted': [8, 6, 4],
            'free_throws_made': [2, 2, 1],
            'free_throws_attempted': [2, 3, 2],
            'steals': [2, 1, 0],
            'blocks': [1, 0, 1],
            'turnovers': [3, 2, 1],
            'minutes_played': [35, 28, 22]
        })
        
        result = aggregator._create_daily_aggregations(input_df, "2023-24", "2024-01-15")
        
        # Verify structure
        assert len(result) == 2  # Two unique players
        assert set(result.columns).issuperset({
            'player_id', 'points', 'rebounds', 'assists', 'field_goal_percentage',
            'three_point_percentage', 'free_throw_percentage', 'season', 'date'
        })
        
        # Verify aggregations for player1 (two games)
        player1_stats = result[result['player_id'] == 'player1'].iloc[0]
        assert player1_stats['points'] == 43  # 25 + 18
        assert player1_stats['rebounds'] == 14  # 8 + 6
        assert player1_stats['assists'] == 8  # 5 + 3
        assert player1_stats['games_played'] == 2
        
        # Verify percentages
        expected_fg_pct = 17 / 35  # (10+7) / (20+15)
        assert abs(player1_stats['field_goal_percentage'] - expected_fg_pct) < 0.001
        
        # Verify aggregations for player2 (one game)
        player2_stats = result[result['player_id'] == 'player2'].iloc[0]
        assert player2_stats['points'] == 12
        assert player2_stats['games_played'] == 1

    @patch('app.aggregator.validate_input_data')
    @patch('app.aggregator.validate_output_data')
    def test_process_silver_file_success(self, mock_validate_output, mock_validate_input):
        """Test successful processing of a Silver file."""
        # Create test data
        test_df = pd.DataFrame({
            'player_id': ['player1', 'player2'],
            'points': [25, 18],
            'rebounds': [8, 6],
            'assists': [5, 3],
            'field_goals_made': [10, 7],
            'field_goals_attempted': [20, 15],
            'three_pointers_made': [3, 2],
            'three_pointers_attempted': [8, 6],
            'free_throws_made': [2, 2],
            'free_throws_attempted': [2, 3],
            'steals': [2, 1],
            'blocks': [1, 0],
            'turnovers': [3, 2],
            'minutes_played': [35, 28]
        })
        
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.read_parquet.return_value = test_df
        mock_s3_client.object_exists.return_value = False  # No existing season stats
        
        # Mock config
        config = LambdaConfig(
            silver_bucket="test-silver",
            gold_bucket="test-gold"
        )
        
        aggregator = PlayerStatsAggregator(config, mock_s3_client)
        
        # Mock the write methods
        aggregator._write_gold_layer_files = Mock(return_value=4)
        
        # Test processing
        result = aggregator.process_silver_file(
            "test-silver",
            "silver/player_games/season=2023-24/date=2024-01-15/player_stats.parquet"
        )
        
        # Verify result
        assert result['players_processed'] == 2
        assert result['files_written'] == 4
        assert result['season'] == "2023-24"
        assert result['date'] == "2024-01-15"
        
        # Verify S3 client was called
        mock_s3_client.read_parquet.assert_called_once()

    def test_update_season_stats_new_players(self):
        """Test updating season stats with new players."""
        aggregator = self._create_aggregator()
        
        # Empty existing season stats
        season_stats = pd.DataFrame(columns=[
            'player_id', 'season', 'games_played', 'points', 'rebounds', 'assists',
            'field_goals_made', 'field_goals_attempted', 'field_goal_percentage',
            'three_pointers_made', 'three_pointers_attempted', 'three_point_percentage',
            'free_throws_made', 'free_throws_attempted', 'free_throw_percentage',
            'steals', 'blocks', 'turnovers', 'minutes_played', 'updated_at'
        ])
        
        # New daily stats
        daily_stats = pd.DataFrame({
            'player_id': ['player1'],
            'season': ['2023-24'],
            'points': [25],
            'rebounds': [8],
            'assists': [5],
            'field_goals_made': [10],
            'field_goals_attempted': [20],
            'field_goal_percentage': [0.5],
            'three_pointers_made': [3],
            'three_pointers_attempted': [8],
            'three_point_percentage': [0.375],
            'free_throws_made': [2],
            'free_throws_attempted': [2],
            'free_throw_percentage': [1.0],
            'steals': [2],
            'blocks': [1],
            'turnovers': [3],
            'minutes_played': [35],
            'games_played': [1],
            'date': ['2024-01-15'],
            'updated_at': ['2024-01-15T10:00:00']
        })
        
        result = aggregator._update_season_stats(season_stats, daily_stats, "2024-01-15")
        
        # Should create new season stats record
        assert len(result) == 1
        assert result.iloc[0]['player_id'] == 'player1'
        assert result.iloc[0]['points'] == 25
        assert result.iloc[0]['games_played'] == 1

    def test_update_season_stats_existing_players(self):
        """Test updating season stats with existing players."""
        aggregator = self._create_aggregator()
        
        # Existing season stats
        season_stats = pd.DataFrame({
            'player_id': ['player1'],
            'season': ['2023-24'],
            'games_played': [5],
            'points': [100],
            'rebounds': [40],
            'assists': [25],
            'field_goals_made': [40],
            'field_goals_attempted': [100],
            'field_goal_percentage': [0.4],
            'three_pointers_made': [10],
            'three_pointers_attempted': [30],
            'three_point_percentage': [0.333],
            'free_throws_made': [10],
            'free_throws_attempted': [15],
            'free_throw_percentage': [0.667],
            'steals': [8],
            'blocks': [3],
            'turnovers': [15],
            'minutes_played': [175],
            'updated_at': ['2024-01-14T10:00:00']
        })
        
        # New daily stats
        daily_stats = pd.DataFrame({
            'player_id': ['player1'],
            'season': ['2023-24'],
            'points': [25],
            'rebounds': [8],
            'assists': [5],
            'field_goals_made': [10],
            'field_goals_attempted': [20],
            'field_goal_percentage': [0.5],
            'three_pointers_made': [3],
            'three_pointers_attempted': [8],
            'three_point_percentage': [0.375],
            'free_throws_made': [2],
            'free_throws_attempted': [2],
            'free_throw_percentage': [1.0],
            'steals': [2],
            'blocks': [1],
            'turnovers': [3],
            'minutes_played': [35],
            'games_played': [1],
            'date': ['2024-01-15'],
            'updated_at': ['2024-01-15T10:00:00']
        })
        
        result = aggregator._update_season_stats(season_stats, daily_stats, "2024-01-15")
        
        # Should update existing stats
        assert len(result) == 1
        player_stats = result.iloc[0]
        assert player_stats['player_id'] == 'player1'
        assert player_stats['points'] == 125  # 100 + 25
        assert player_stats['games_played'] == 6  # 5 + 1
        assert player_stats['rebounds'] == 48  # 40 + 8
        
        # Verify percentage recalculation
        expected_fg_pct = 50 / 120  # (40+10) / (100+20)
        assert abs(player_stats['field_goal_percentage'] - expected_fg_pct) < 0.001

    def _create_aggregator(self):
        """Helper method to create aggregator with test config."""
        config = LambdaConfig(
            silver_bucket="test-silver",
            gold_bucket="test-gold"
        )
        mock_s3_client = Mock()
        return PlayerStatsAggregator(config, mock_s3_client)