"""
Core aggregation functions for player daily statistics.

Implements basic aggregations and shooting percentage calculations
following the Silver-to-Gold ETL pattern.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def aggregate_daily_stats(player_games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate player game data into daily statistics.
    
    Args:
        player_games_df: DataFrame with individual player game records
        
    Returns:
        DataFrame with daily aggregated statistics per player
    """
    if player_games_df.empty:
        return pd.DataFrame()
    
    # Basic counting stats aggregation
    agg_functions = {
        'points': 'sum',
        'rebounds': 'sum',
        'assists': 'sum',
        'steals': 'sum',
        'blocks': 'sum',
        'turnovers': 'sum',
        'field_goals_made': 'sum',
        'field_goals_attempted': 'sum',
        'three_pointers_made': 'sum',
        'three_pointers_attempted': 'sum',
        'free_throws_made': 'sum',
        'free_throws_attempted': 'sum',
        'minutes_played': 'sum',
        'game_id': 'count'  # Count of games played
    }
    
    # Group by player_id and aggregate
    daily_stats = player_games_df.groupby('player_id').agg(agg_functions).reset_index()
    
    # Rename game count column
    daily_stats = daily_stats.rename(columns={'game_id': 'games_played'})
    
    # Calculate shooting percentages
    daily_stats = calculate_shooting_percentages(daily_stats)
    
    # Add metadata columns
    if 'season' in player_games_df.columns:
        daily_stats['season'] = player_games_df['season'].iloc[0]
    if 'game_date' in player_games_df.columns:
        daily_stats['date'] = player_games_df['game_date'].iloc[0]
        
    return daily_stats


def calculate_shooting_percentages(stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate shooting percentages from made/attempted statistics.
    
    Args:
        stats_df: DataFrame with made/attempted shooting statistics
        
    Returns:
        DataFrame with added shooting percentage columns
    """
    stats_df = stats_df.copy()
    
    # Field goal percentage
    if 'field_goals_made' in stats_df.columns and 'field_goals_attempted' in stats_df.columns:
        stats_df['fg_percentage'] = np.where(
            stats_df['field_goals_attempted'] > 0,
            stats_df['field_goals_made'] / stats_df['field_goals_attempted'],
            0.0
        )
    
    # Three-point percentage  
    if 'three_pointers_made' in stats_df.columns and 'three_pointers_attempted' in stats_df.columns:
        stats_df['three_point_percentage'] = np.where(
            stats_df['three_pointers_attempted'] > 0,
            stats_df['three_pointers_made'] / stats_df['three_pointers_attempted'],
            0.0
        )
    
    # Free throw percentage
    if 'free_throws_made' in stats_df.columns and 'free_throws_attempted' in stats_df.columns:
        stats_df['free_throw_percentage'] = np.where(
            stats_df['free_throws_attempted'] > 0,
            stats_df['free_throws_made'] / stats_df['free_throws_attempted'],
            0.0
        )
    
    return stats_df


def calculate_season_to_date_stats(
    daily_stats_df: pd.DataFrame, 
    existing_season_stats_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Calculate cumulative season-to-date statistics.
    
    Args:
        daily_stats_df: Daily statistics for current date
        existing_season_stats_df: Previously accumulated season stats
        
    Returns:
        DataFrame with updated season-to-date statistics
    """
    if existing_season_stats_df is None or existing_season_stats_df.empty:
        # First day of season, daily stats are season stats
        season_stats = daily_stats_df.copy()
    else:
        # Merge with existing season stats
        season_stats = _accumulate_season_stats(daily_stats_df, existing_season_stats_df)
    
    # Recalculate shooting percentages for season totals
    season_stats = calculate_shooting_percentages(season_stats)
    
    return season_stats


def _accumulate_season_stats(
    daily_stats_df: pd.DataFrame, 
    existing_stats_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Accumulate daily stats with existing season stats.
    
    Args:
        daily_stats_df: Daily statistics to add
        existing_stats_df: Existing season statistics
        
    Returns:
        DataFrame with accumulated statistics
    """
    # Columns to sum up (cumulative counting stats)
    sum_columns = [
        'points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers',
        'field_goals_made', 'field_goals_attempted',
        'three_pointers_made', 'three_pointers_attempted',
        'free_throws_made', 'free_throws_attempted',
        'minutes_played', 'games_played'
    ]
    
    # Merge on player_id
    merged = pd.merge(
        daily_stats_df[['player_id'] + sum_columns],
        existing_stats_df[['player_id'] + sum_columns],
        on='player_id',
        how='outer',
        suffixes=('_daily', '_season')
    )
    
    # Sum the statistics
    result = pd.DataFrame()
    result['player_id'] = merged['player_id']
    
    for col in sum_columns:
        daily_col = f"{col}_daily"
        season_col = f"{col}_season"
        result[col] = merged[daily_col].fillna(0) + merged[season_col].fillna(0)
    
    # Preserve metadata from daily stats
    if 'season' in daily_stats_df.columns:
        result['season'] = daily_stats_df['season'].iloc[0]
    if 'date' in daily_stats_df.columns:
        result['date'] = daily_stats_df['date'].iloc[0]
        
    return result


def validate_aggregated_data(stats_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform basic validation on aggregated statistics.
    
    Args:
        stats_df: DataFrame with aggregated statistics
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'total_records': len(stats_df),
        'validation_passed': True,
        'issues': []
    }
    
    if stats_df.empty:
        validation_results['validation_passed'] = False
        validation_results['issues'].append('No data to validate')
        return validation_results
    
    # Check for null player_ids
    null_player_ids = stats_df['player_id'].isnull().sum()
    if null_player_ids > 0:
        validation_results['issues'].append(f'{null_player_ids} records with null player_id')
        validation_results['validation_passed'] = False
    
    # Check for negative statistics (shouldn't happen with proper aggregation)
    numeric_columns = ['points', 'rebounds', 'assists', 'steals', 'blocks']
    for col in numeric_columns:
        if col in stats_df.columns:
            negative_count = (stats_df[col] < 0).sum()
            if negative_count > 0:
                validation_results['issues'].append(f'{negative_count} records with negative {col}')
                validation_results['validation_passed'] = False
    
    # Check shooting percentage ranges (0-1)
    percentage_columns = ['fg_percentage', 'three_point_percentage', 'free_throw_percentage']
    for col in percentage_columns:
        if col in stats_df.columns:
            invalid_pct = ((stats_df[col] < 0) | (stats_df[col] > 1)).sum()
            if invalid_pct > 0:
                validation_results['issues'].append(f'{invalid_pct} records with invalid {col}')
                validation_results['validation_passed'] = False
    
    return validation_results