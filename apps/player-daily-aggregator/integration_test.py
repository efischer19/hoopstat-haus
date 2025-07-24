"""Integration test for season stats updates."""

from unittest.mock import Mock

import pandas as pd

from app.aggregator import PlayerStatsAggregator
from app.config import LambdaConfig


def test_season_stats_accumulation():
    """Test that season stats correctly accumulate over multiple games."""
    print("🏀 Testing Season Stats Accumulation")
    print("=" * 50)

    # Mock S3 client that simulates existing season data
    mock_s3_client = Mock()

    # Day 1: First game data
    day1_data = pd.DataFrame(
        {
            "player_id": ["lebron_james"],
            "points": [28],
            "rebounds": [10],
            "assists": [7],
            "field_goals_made": [11],
            "field_goals_attempted": [20],
            "three_pointers_made": [3],
            "three_pointers_attempted": [8],
            "free_throws_made": [3],
            "free_throws_attempted": [4],
            "steals": [2],
            "blocks": [1],
            "turnovers": [4],
            "minutes_played": [38],
        }
    )

    # Simulate no existing season stats (first game of season)
    config = LambdaConfig(silver_bucket="test", gold_bucket="test")
    aggregator = PlayerStatsAggregator(config, mock_s3_client)

    # Process Day 1
    mock_s3_client.object_exists.return_value = False
    daily_stats_day1 = aggregator._create_daily_aggregations(
        day1_data, "2023-24", "2024-01-15"
    )
    season_stats_empty = pd.DataFrame(
        columns=[
            "player_id",
            "season",
            "games_played",
            "points",
            "rebounds",
            "assists",
            "field_goals_made",
            "field_goals_attempted",
            "field_goal_percentage",
            "three_pointers_made",
            "three_pointers_attempted",
            "three_point_percentage",
            "free_throws_made",
            "free_throws_attempted",
            "free_throw_percentage",
            "steals",
            "blocks",
            "turnovers",
            "minutes_played",
            "updated_at",
        ]
    )

    season_stats_after_day1 = aggregator._update_season_stats(
        season_stats_empty, daily_stats_day1, "2024-01-15"
    )

    print("After Day 1:")
    display_cols = [
        "player_id",
        "points",
        "rebounds",
        "assists",
        "games_played",
        "field_goal_percentage",
    ]
    print(season_stats_after_day1[display_cols].round(3).to_string(index=False))

    # Day 2: Second game data
    day2_data = pd.DataFrame(
        {
            "player_id": ["lebron_james"],
            "points": [31],
            "rebounds": [8],
            "assists": [9],
            "field_goals_made": [12],
            "field_goals_attempted": [22],
            "three_pointers_made": [4],
            "three_pointers_attempted": [9],
            "free_throws_made": [3],
            "free_throws_attempted": [4],
            "steals": [1],
            "blocks": [0],
            "turnovers": [3],
            "minutes_played": [35],
        }
    )

    # Process Day 2 with existing season stats
    daily_stats_day2 = aggregator._create_daily_aggregations(
        day2_data, "2023-24", "2024-01-16"
    )
    season_stats_after_day2 = aggregator._update_season_stats(
        season_stats_after_day1, daily_stats_day2, "2024-01-16"
    )

    print("\nAfter Day 2:")
    print(season_stats_after_day2[display_cols].round(3).to_string(index=False))

    # Verify calculations
    player_stats = season_stats_after_day2.iloc[0]

    # Expected totals
    expected_points = 28 + 31  # 59
    expected_games = 2
    expected_fg_made = 11 + 12  # 23
    expected_fg_pct = 23 / 42  # ~0.548

    print("\n📊 Verification:")
    print(f"  Total Points: {player_stats['points']} (expected: {expected_points})")
    print(
        f"  Games Played: {player_stats['games_played']} (expected: {expected_games})"
    )
    print(
        f"  FG Made: {player_stats['field_goals_made']} (expected: {expected_fg_made})"
    )
    print(
        f"  FG%: {player_stats['field_goal_percentage']:.3f} "
        f"(expected: {expected_fg_pct:.3f})"
    )

    # Assertions
    assert player_stats["points"] == expected_points, (
        f"Points mismatch: {player_stats['points']} != {expected_points}"
    )
    assert player_stats["games_played"] == expected_games, (
        f"Games mismatch: {player_stats['games_played']} != {expected_games}"
    )
    assert abs(player_stats["field_goal_percentage"] - expected_fg_pct) < 0.001, (
        "FG% mismatch"
    )

    print("\n✅ Season stats accumulation working correctly!")


def test_multiple_players_same_day():
    """Test processing multiple players in the same day."""
    print("\n🏀 Testing Multiple Players Same Day")
    print("=" * 45)

    # Sample data with multiple players
    multi_player_data = pd.DataFrame(
        {
            "player_id": [
                "lebron_james",
                "stephen_curry",
                "kevin_durant",
                "lebron_james",
            ],
            "game_id": ["game_1", "game_1", "game_1", "game_2"],  # LeBron plays twice
            "points": [28, 35, 27, 22],
            "rebounds": [10, 5, 9, 6],
            "assists": [7, 8, 4, 11],
            "field_goals_made": [11, 13, 10, 8],
            "field_goals_attempted": [20, 24, 18, 16],
            "three_pointers_made": [3, 7, 2, 2],
            "three_pointers_attempted": [8, 15, 6, 5],
            "free_throws_made": [3, 2, 5, 4],
            "free_throws_attempted": [4, 2, 6, 4],
            "steals": [2, 3, 1, 3],
            "blocks": [1, 0, 2, 0],
            "turnovers": [4, 2, 3, 2],
            "minutes_played": [38, 42, 40, 28],
        }
    )

    config = LambdaConfig(silver_bucket="test", gold_bucket="test")
    mock_s3_client = Mock()
    aggregator = PlayerStatsAggregator(config, mock_s3_client)

    # Process the day
    daily_stats = aggregator._create_daily_aggregations(
        multi_player_data, "2023-24", "2024-01-15"
    )

    print("Daily aggregations for multiple players:")
    display_cols = [
        "player_id",
        "points",
        "rebounds",
        "assists",
        "games_played",
        "field_goal_percentage",
    ]
    print(daily_stats[display_cols].round(3).to_string(index=False))

    # Verify LeBron's stats (he played 2 games)
    lebron_stats = daily_stats[daily_stats["player_id"] == "lebron_james"].iloc[0]
    assert lebron_stats["games_played"] == 2, (
        f"LeBron should have 2 games, got {lebron_stats['games_played']}"
    )
    assert lebron_stats["points"] == 50, (
        f"LeBron should have 50 points (28+22), got {lebron_stats['points']}"
    )

    # Verify others played once
    for player in ["stephen_curry", "kevin_durant"]:
        player_stats = daily_stats[daily_stats["player_id"] == player].iloc[0]
        assert player_stats["games_played"] == 1, f"{player} should have 1 game"

    print("\n✅ Multiple player processing working correctly!")


if __name__ == "__main__":
    print("🏀 Player Daily Aggregator - Integration Tests")
    print("=" * 55)

    test_season_stats_accumulation()
    test_multiple_players_same_day()

    print("\n🎉 All integration tests passed!")
    print("🚀 The Lambda function is production ready!")
