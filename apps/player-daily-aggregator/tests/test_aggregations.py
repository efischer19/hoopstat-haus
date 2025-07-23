"""Tests for aggregations module."""

import pytest
import numpy as np
import pandas as pd

from player_daily_aggregator.aggregations import (
    aggregate_daily_stats,
    calculate_shooting_percentages,
    calculate_season_to_date_stats,
    validate_aggregated_data
)


class TestAggregateDailyStats:
    """Test cases for daily statistics aggregation."""
    
    def test_basic_daily_aggregation(self):
        """Test basic aggregation of player game data."""
        # Create sample player game data
        game_data = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'steals': 2,
                'blocks': 1,
                'turnovers': 3,
                'field_goals_made': 10,
                'field_goals_attempted': 20,
                'three_pointers_made': 3,
                'three_pointers_attempted': 8,
                'free_throws_made': 2,
                'free_throws_attempted': 2,
                'minutes_played': 35.5,
                'game_id': 'game1',
                'season': '2023-24',
                'game_date': '2024-01-15'
            },
            {
                'player_id': 'player2',
                'points': 15,
                'rebounds': 12,
                'assists': 3,
                'steals': 1,
                'blocks': 2,
                'turnovers': 2,
                'field_goals_made': 6,
                'field_goals_attempted': 15,
                'three_pointers_made': 1,
                'three_pointers_attempted': 5,
                'free_throws_made': 2,
                'free_throws_attempted': 3,
                'minutes_played': 32.0,
                'game_id': 'game1',
                'season': '2023-24',
                'game_date': '2024-01-15'
            }
        ])
        
        result = aggregate_daily_stats(game_data)
        
        assert len(result) == 2
        assert 'player1' in result['player_id'].values
        assert 'player2' in result['player_id'].values
        
        # Check player1 stats
        player1_stats = result[result['player_id'] == 'player1'].iloc[0]
        assert player1_stats['points'] == 25
        assert player1_stats['rebounds'] == 8
        assert player1_stats['assists'] == 5
        assert player1_stats['games_played'] == 1
        
        # Check that shooting percentages are calculated
        assert 'fg_percentage' in result.columns
        assert 'three_point_percentage' in result.columns
        assert 'free_throw_percentage' in result.columns
    
    def test_multiple_games_aggregation(self):
        """Test aggregation across multiple games for same player."""
        game_data = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 20,
                'rebounds': 5,
                'assists': 7,
                'steals': 1,
                'blocks': 0,
                'turnovers': 2,
                'field_goals_made': 8,
                'field_goals_attempted': 16,
                'three_pointers_made': 2,
                'three_pointers_attempted': 6,
                'free_throws_made': 2,
                'free_throws_attempted': 2,
                'minutes_played': 30.0,
                'game_id': 'game1',
                'season': '2023-24',
                'game_date': '2024-01-15'
            },
            {
                'player_id': 'player1',
                'points': 30,
                'rebounds': 10,
                'assists': 3,
                'steals': 3,
                'blocks': 2,
                'turnovers': 4,
                'field_goals_made': 12,
                'field_goals_attempted': 20,
                'three_pointers_made': 4,
                'three_pointers_attempted': 8,
                'free_throws_made': 2,
                'free_throws_attempted': 4,
                'minutes_played': 35.0,
                'game_id': 'game2',
                'season': '2023-24',
                'game_date': '2024-01-15'
            }
        ])
        
        result = aggregate_daily_stats(game_data)
        
        assert len(result) == 1
        player_stats = result.iloc[0]
        
        # Check aggregated totals
        assert player_stats['points'] == 50  # 20 + 30
        assert player_stats['rebounds'] == 15  # 5 + 10
        assert player_stats['assists'] == 10  # 7 + 3
        assert player_stats['games_played'] == 2
        assert player_stats['field_goals_made'] == 20  # 8 + 12
        assert player_stats['field_goals_attempted'] == 36  # 16 + 20
    
    def test_empty_data(self):
        """Test aggregation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = aggregate_daily_stats(empty_df)
        assert result.empty


class TestCalculateShootingPercentages:
    """Test cases for shooting percentage calculations."""
    
    def test_valid_shooting_percentages(self):
        """Test calculation of shooting percentages."""
        stats_df = pd.DataFrame([
            {
                'player_id': 'player1',
                'field_goals_made': 10,
                'field_goals_attempted': 20,
                'three_pointers_made': 3,
                'three_pointers_attempted': 8,
                'free_throws_made': 8,
                'free_throws_attempted': 10
            }
        ])
        
        result = calculate_shooting_percentages(stats_df)
        
        assert result['fg_percentage'].iloc[0] == 0.5  # 10/20
        assert result['three_point_percentage'].iloc[0] == 0.375  # 3/8
        assert result['free_throw_percentage'].iloc[0] == 0.8  # 8/10
    
    def test_zero_attempts_handling(self):
        """Test handling of zero attempts in shooting percentages."""
        stats_df = pd.DataFrame([
            {
                'player_id': 'player1',
                'field_goals_made': 0,
                'field_goals_attempted': 0,
                'three_pointers_made': 0,
                'three_pointers_attempted': 0,
                'free_throws_made': 0,
                'free_throws_attempted': 0
            }
        ])
        
        result = calculate_shooting_percentages(stats_df)
        
        assert result['fg_percentage'].iloc[0] == 0.0
        assert result['three_point_percentage'].iloc[0] == 0.0
        assert result['free_throw_percentage'].iloc[0] == 0.0


class TestCalculateSeasonToDateStats:
    """Test cases for season-to-date statistics."""
    
    def test_first_day_of_season(self):
        """Test season stats calculation for first day."""
        daily_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'games_played': 1,
                'field_goals_made': 10,
                'field_goals_attempted': 20
            }
        ])
        
        result = calculate_season_to_date_stats(daily_stats)
        
        # First day should equal daily stats
        assert result['points'].iloc[0] == 25
        assert result['rebounds'].iloc[0] == 8
        assert result['games_played'].iloc[0] == 1
    
    def test_accumulation_with_existing_stats(self):
        """Test accumulation with existing season statistics."""
        daily_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'games_played': 1,
                'field_goals_made': 10,
                'field_goals_attempted': 20,
                'steals': 2,
                'blocks': 1,
                'turnovers': 3,
                'three_pointers_made': 3,
                'three_pointers_attempted': 8,
                'free_throws_made': 2,
                'free_throws_attempted': 2,
                'minutes_played': 35.0
            }
        ])
        
        existing_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 100,
                'rebounds': 40,
                'assists': 25,
                'games_played': 4,
                'field_goals_made': 40,
                'field_goals_attempted': 80,
                'steals': 8,
                'blocks': 4,
                'turnovers': 12,
                'three_pointers_made': 12,
                'three_pointers_attempted': 32,
                'free_throws_made': 8,
                'free_throws_attempted': 10,
                'minutes_played': 140.0
            }
        ])
        
        result = calculate_season_to_date_stats(daily_stats, existing_stats)
        
        # Check accumulated totals
        assert result['points'].iloc[0] == 125  # 25 + 100
        assert result['rebounds'].iloc[0] == 48  # 8 + 40
        assert result['games_played'].iloc[0] == 5  # 1 + 4
        assert result['field_goals_made'].iloc[0] == 50  # 10 + 40


class TestValidateAggregatedData:
    """Test cases for data validation."""
    
    def test_valid_data_passes_validation(self):
        """Test that valid data passes validation."""
        valid_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'rebounds': 8,
                'assists': 5,
                'steals': 2,
                'blocks': 1,
                'fg_percentage': 0.5,
                'three_point_percentage': 0.375,
                'free_throw_percentage': 0.8
            }
        ])
        
        result = validate_aggregated_data(valid_stats)
        
        assert result['validation_passed'] is True
        assert result['total_records'] == 1
        assert len(result['issues']) == 0
    
    def test_null_player_id_detected(self):
        """Test detection of null player IDs."""
        invalid_stats = pd.DataFrame([
            {
                'player_id': None,
                'points': 25,
                'rebounds': 8,
                'assists': 5
            }
        ])
        
        result = validate_aggregated_data(invalid_stats)
        
        assert result['validation_passed'] is False
        assert '1 records with null player_id' in result['issues']
    
    def test_negative_stats_detected(self):
        """Test detection of negative statistics."""
        invalid_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': -5,
                'rebounds': 8,
                'assists': 5
            }
        ])
        
        result = validate_aggregated_data(invalid_stats)
        
        assert result['validation_passed'] is False
        assert '1 records with negative points' in result['issues']
    
    def test_invalid_shooting_percentages_detected(self):
        """Test detection of invalid shooting percentages."""
        invalid_stats = pd.DataFrame([
            {
                'player_id': 'player1',
                'points': 25,
                'fg_percentage': 1.5,  # Invalid - over 100%
                'three_point_percentage': -0.1  # Invalid - negative
            }
        ])
        
        result = validate_aggregated_data(invalid_stats)
        
        assert result['validation_passed'] is False
        assert '1 records with invalid fg_percentage' in result['issues']
        assert '1 records with invalid three_point_percentage' in result['issues']
    
    def test_empty_data_validation(self):
        """Test validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = validate_aggregated_data(empty_df)
        
        assert result['validation_passed'] is False
        assert 'No data to validate' in result['issues']