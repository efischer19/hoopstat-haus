"""Tests for data models."""

import pytest
from pydantic import ValidationError

from hoopstat_data.models import GameStats, PlayerStats, TeamStats


class TestPlayerStats:
    """Test cases for PlayerStats model."""

    def test_valid_player_stats(self):
        """Test creating valid player stats."""
        stats = PlayerStats(
            player_id="12345",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert stats.player_id == "12345"
        assert stats.points == 25
        assert stats.rebounds == 10
        assert stats.assists == 5

    def test_player_stats_with_optional_fields(self):
        """Test player stats with optional shooting stats."""
        stats = PlayerStats(
            player_id="12345",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            field_goals_made=10,
            field_goals_attempted=15,
            minutes_played=35.5,
        )

        assert stats.field_goals_made == 10
        assert stats.field_goals_attempted == 15
        assert stats.minutes_played == 35.5

    def test_negative_stats_validation(self):
        """Test that negative stats are rejected."""
        with pytest.raises(ValidationError):
            PlayerStats(
                player_id="12345",
                points=-5,  # Invalid negative value
                rebounds=10,
                assists=5,
            )

    def test_field_goals_consistency(self):
        """Test that field goals made cannot exceed attempted."""
        with pytest.raises(ValidationError):
            PlayerStats(
                player_id="12345",
                points=25,
                rebounds=10,
                assists=5,
                field_goals_made=15,
                field_goals_attempted=10,  # Less than made
            )

    def test_minimal_required_fields(self):
        """Test creating stats with only required fields."""
        stats = PlayerStats(
            player_id="12345",
            points=0,
            rebounds=0,
            assists=0,
            steals=0,
            blocks=0,
            turnovers=0,
        )

        assert stats.player_id == "12345"
        assert stats.points == 0


class TestTeamStats:
    """Test cases for TeamStats model."""

    def test_valid_team_stats(self):
        """Test creating valid team stats."""
        stats = TeamStats(
            team_id="lakers_001",
            team_name="Lakers",
            points=120,
            field_goals_made=45,
            field_goals_attempted=90,
            rebounds=50,
            assists=25,
        )

        assert stats.team_id == "lakers_001"
        assert stats.team_name == "Lakers"
        assert stats.points == 120

    def test_negative_team_stats_validation(self):
        """Test that negative team stats are rejected."""
        with pytest.raises(ValidationError):
            TeamStats(
                team_id="lakers_001",
                team_name="Lakers",
                points=-120,  # Invalid negative value
                field_goals_made=45,
                field_goals_attempted=90,
                rebounds=50,
                assists=25,
            )


class TestGameStats:
    """Test cases for GameStats model."""

    def test_valid_game_stats(self):
        """Test creating valid game stats."""
        stats = GameStats(
            game_id="game_12345",
            home_team_id="lakers_001",
            away_team_id="celtics_001",
            home_score=110,
            away_score=105,
        )

        assert stats.game_id == "game_12345"
        assert stats.home_score == 110
        assert stats.away_score == 105

    def test_game_stats_with_metadata(self):
        """Test game stats with optional metadata."""
        stats = GameStats(
            game_id="game_12345",
            home_team_id="lakers_001",
            away_team_id="celtics_001",
            home_score=110,
            away_score=105,
            season="2023-24",
            game_date="2024-01-15",
            venue="Crypto.com Arena",
            quarters=4,
            overtime=False,
        )

        assert stats.season == "2023-24"
        assert stats.venue == "Crypto.com Arena"
        assert stats.quarters == 4
        assert stats.overtime is False

    def test_negative_scores_validation(self):
        """Test that negative scores are rejected."""
        with pytest.raises(ValidationError):
            GameStats(
                game_id="game_12345",
                home_team_id="lakers_001",
                away_team_id="celtics_001",
                home_score=-110,  # Invalid negative score
                away_score=105,
            )

    def test_quarters_validation(self):
        """Test quarters validation (minimum 4, maximum 8)."""
        # Valid quarters
        stats = GameStats(
            game_id="game_12345",
            home_team_id="lakers_001",
            away_team_id="celtics_001",
            home_score=110,
            away_score=105,
            quarters=5,  # Overtime game
        )
        assert stats.quarters == 5

        # Invalid quarters (too few)
        with pytest.raises(ValidationError):
            GameStats(
                game_id="game_12345",
                home_team_id="lakers_001",
                away_team_id="celtics_001",
                home_score=110,
                away_score=105,
                quarters=3,  # Too few quarters
            )
