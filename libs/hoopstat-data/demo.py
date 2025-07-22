#!/usr/bin/env python3
"""
Demo script for hoopstat-data processing utilities.

This script demonstrates the key functionality of the data processing library.
"""

from hoopstat_data import (
    GameStats,
    PlayerStats,
    TeamStats,
    calculate_efficiency_rating,
    check_data_completeness,
    detect_outliers,
    normalize_team_name,
    standardize_position,
    validate_player_stats,
)


def demo_data_models():
    """Demonstrate data models."""
    print("=== Data Models Demo ===")

    # Player stats model
    player = PlayerStats(
        player_id="player_001",
        player_name="LeBron James",
        team="Lakers",
        position="Small Forward",
        points=27,
        rebounds=8,
        assists=8,
        steals=1,
        blocks=1,
        turnovers=4,
        field_goals_made=10,
        field_goals_attempted=18,
        minutes_played=38.5,
    )
    print(
        f"Player: {player.player_name} - {player.points} pts, "
        f"{player.rebounds} reb, {player.assists} ast"
    )

    # Team stats model
    team = TeamStats(
        team_id="lakers_001",
        team_name="Los Angeles Lakers",
        points=112,
        field_goals_made=42,
        field_goals_attempted=88,
        rebounds=45,
        assists=28,
    )
    print(f"Team: {team.team_name} - {team.points} pts, {team.rebounds} reb")

    # Game stats model
    game = GameStats(
        game_id="game_20240115",
        home_team_id="lakers_001",
        away_team_id="celtics_001",
        home_score=112,
        away_score=109,
        season="2023-24",
    )
    print(f"Game: {game.home_score} - {game.away_score}")
    print()


def demo_validation():
    """Demonstrate validation functions."""
    print("=== Validation Demo ===")

    # Valid player stats
    valid_stats = {"points": 25, "rebounds": 10, "assists": 5, "steals": 2}
    print(f"Valid stats: {validate_player_stats(valid_stats)}")

    # Invalid player stats (negative rebounds)
    invalid_stats = {"points": 25, "rebounds": -5, "assists": 5}
    print(f"Invalid stats: {validate_player_stats(invalid_stats)}")

    # Missing required fields
    incomplete_stats = {"points": 25}
    print(f"Incomplete stats: {validate_player_stats(incomplete_stats)}")
    print()


def demo_transformations():
    """Demonstrate transformation functions."""
    print("=== Transformations Demo ===")

    # Team name normalization
    team_names = ["LA Lakers", "lakers", "Los Angeles Lakers", "golden state warriors"]
    for name in team_names:
        normalized = normalize_team_name(name)
        print(f"'{name}' -> '{normalized}'")

    print()

    # Position standardization
    positions = ["Point Guard", "shooting guard", "SF", "center", "Unknown Position"]
    for pos in positions:
        standardized = standardize_position(pos)
        print(f"'{pos}' -> '{standardized}'")

    print()

    # Efficiency rating calculation
    player_stats = {
        "points": 28,
        "rebounds": 12,
        "assists": 6,
        "steals": 2,
        "blocks": 1,
        "turnovers": 3,
        "minutes_played": 42,
    }
    efficiency = calculate_efficiency_rating(player_stats)
    print(f"Player efficiency rating: {efficiency}")
    print()


def demo_quality_checking():
    """Demonstrate data quality functions."""
    print("=== Data Quality Demo ===")

    # Data completeness check
    incomplete_data = {"points": 25, "rebounds": None, "assists": 5}
    completeness = check_data_completeness(incomplete_data)
    print(f"Completeness check: {completeness}")

    # Outlier detection
    scoring_data = [15, 18, 22, 19, 21, 16, 20, 85, 17, 19]  # 85 is an outlier
    outliers = detect_outliers(scoring_data)
    print(f"Outliers in scoring data {scoring_data}: indices {outliers}")
    print()


def main():
    """Run all demos."""
    print("Hoopstat Data Processing Utilities Demo")
    print("=" * 50)
    print()

    demo_data_models()
    demo_validation()
    demo_transformations()
    demo_quality_checking()

    print("Demo completed successfully!")


if __name__ == "__main__":
    main()
