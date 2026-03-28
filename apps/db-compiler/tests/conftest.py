"""Shared pytest fixtures for db-compiler tests."""

from pathlib import Path

import pytest

from app.fetcher import GoldDataset

# Path to the fixture JSON files used in fetcher tests
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_dataset() -> GoldDataset:
    """Return a small but complete GoldDataset for writer / validator tests."""
    return GoldDataset(
        player_daily_stats=[
            {
                "player_id": "2544",
                "player_name": "LeBron James",
                "team": "LAL",
                "position": "SF",
                "game_id": "0022400001",
                "game_date": "2024-01-15",
                "season": "2024-25",
                "points": 28,
                "rebounds": 8,
                "assists": 6,
                "steals": 1,
                "blocks": 0,
                "turnovers": 3,
                "field_goals_made": 10,
                "field_goals_attempted": 20,
                "three_pointers_made": 2,
                "three_pointers_attempted": 6,
                "free_throws_made": 6,
                "free_throws_attempted": 8,
                "minutes_played": 36.0,
                "efficiency_rating": 22.5,
                "true_shooting_percentage": 0.588,
                "usage_rate": 0.32,
                "plus_minus": 8,
            },
            {
                "player_id": "1234",
                "player_name": "Test Player",
                "team": "BOS",
                "position": "PG",
                "game_id": "0022400002",
                "game_date": "2024-01-15",
                "season": "2024-25",
                "points": 22,
                "rebounds": 4,
                "assists": 9,
                "steals": 2,
                "blocks": 0,
                "turnovers": 2,
                "field_goals_made": 8,
                "field_goals_attempted": 17,
                "three_pointers_made": 3,
                "three_pointers_attempted": 8,
                "free_throws_made": 3,
                "free_throws_attempted": 4,
                "minutes_played": 33.0,
                "efficiency_rating": 18.2,
                "true_shooting_percentage": 0.612,
                "usage_rate": 0.27,
                "plus_minus": -3,
            },
        ],
        team_daily_stats=[
            {
                "team_id": "1610612747",
                "team_name": "Los Angeles Lakers",
                "game_id": "0022400001",
                "game_date": "2024-01-15",
                "season": "2024-25",
                "points": 112,
                "field_goals_made": 42,
                "field_goals_attempted": 90,
                "three_pointers_made": 14,
                "three_pointers_attempted": 35,
                "free_throws_made": 14,
                "free_throws_attempted": 20,
                "rebounds": 45,
                "assists": 26,
                "steals": 8,
                "blocks": 5,
                "turnovers": 12,
                "fouls": 18,
                "offensive_rating": 112.5,
                "defensive_rating": 108.2,
                "pace": 98.5,
                "true_shooting_percentage": 0.612,
                "opponent_team_id": "1610612744",
                "home_game": True,
                "win": True,
            }
        ],
        player_season_summary=[
            {
                "player_id": "2544",
                "player_name": "LeBron James",
                "season": "2024-25",
                "team": "LAL",
                "total_games": 50,
                "total_minutes": 1680.0,
                "points_per_game": 24.5,
                "rebounds_per_game": 7.2,
                "assists_per_game": 8.1,
                "steals_per_game": 1.2,
                "blocks_per_game": 0.8,
                "turnovers_per_game": 3.1,
                "field_goal_percentage": 0.522,
                "three_point_percentage": 0.412,
                "free_throw_percentage": 0.755,
                "efficiency_rating": 28.5,
                "true_shooting_percentage": 0.623,
                "usage_rate": 0.295,
                "scoring_trend": 0.05,
                "efficiency_trend": 0.02,
            }
        ],
        team_season_summary=[
            {
                "team_id": "1610612747",
                "team_name": "Los Angeles Lakers",
                "season": "2024-25",
                "season_type": "regular",
                "total_games": 82,
                "total_points": 9200,
                "total_points_allowed": 8950,
                "points_per_game": 112.2,
                "points_allowed_per_game": 109.1,
                "assists_per_game": 26.5,
                "total_rebounds_per_game": 44.2,
                "turnovers_per_game": 13.5,
                "field_goal_percentage": 0.492,
                "three_point_percentage": 0.362,
                "free_throw_percentage": 0.755,
                "true_shooting_percentage": 0.572,
                "effective_field_goal_percentage": 0.532,
                "offensive_rating": 112.5,
                "defensive_rating": 109.2,
                "net_rating": 3.3,
                "pace": 98.5,
                "turnover_percentage": 0.128,
                "offensive_rebound_percentage": 0.265,
                "free_throw_rate": 0.225,
                "data_quality_score": 0.98,
            }
        ],
        top_lists=[
            {
                "metric": "Points Leaders",
                "list_date": "2024-01-15",
                "rank": 1,
                "player_id": "2544",
                "player_name": "LeBron James",
                "team": "LAL",
                "value": 38.0,
            },
            {
                "metric": "Points Leaders",
                "list_date": "2024-01-15",
                "rank": 2,
                "player_id": "1234",
                "player_name": "Test Player",
                "team": "BOS",
                "value": 32.0,
            },
        ],
    )
