"""
Tests for Gold layer data models.
"""


import pytest

from hoopstat_data.models import (
    DataLineage,
    GoldPlayerDailyStats,
    GoldPlayerSeasonSummary,
    GoldTeamDailyStats,
    ValidationMode,
)


class TestBaseGoldModel:
    """Test base Gold layer model functionality."""

    def test_gold_model_lineage_creation(self):
        """Test that Gold models automatically set transformation stage."""
        # Create a concrete Gold model instance
        gold_stats = GoldPlayerDailyStats(
            player_id="test_player",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert gold_stats.lineage is not None
        assert gold_stats.lineage.transformation_stage == "gold"
        assert gold_stats.lineage.source_system == "silver-to-gold-etl"

    def test_gold_model_with_existing_lineage(self):
        """Test Gold model with provided lineage updates transformation stage."""
        lineage = DataLineage(
            source_system="test-system",
            schema_version="1.0.0",
            transformation_stage="silver",  # Will be updated to gold
            validation_mode=ValidationMode.STRICT,
        )

        gold_stats = GoldPlayerDailyStats(
            player_id="test_player",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            lineage=lineage,
        )

        assert gold_stats.lineage.transformation_stage == "gold"
        assert gold_stats.lineage.source_system == "test-system"


class TestGoldPlayerDailyStats:
    """Test Gold layer player daily statistics model."""

    def test_valid_gold_player_daily_stats(self):
        """Test creating valid Gold player daily stats."""
        stats = GoldPlayerDailyStats(
            player_id="2544",
            player_name="LeBron James",
            team="LAL",
            position="SF",
            points=28,
            rebounds=8,
            assists=7,
            steals=1,
            blocks=1,
            turnovers=4,
            field_goals_made=10,
            field_goals_attempted=20,
            three_pointers_made=2,
            three_pointers_attempted=6,
            free_throws_made=6,
            free_throws_attempted=8,
            minutes_played=38.5,
            game_id="0022300123",
            game_date="2024-01-15",
            efficiency_rating=1.15,
            true_shooting_percentage=0.625,
            usage_rate=0.28,
            plus_minus=8,
            partition_key="season=2023-24/player_id=2544/date=2024-01-15",
            season="2023-24",
        )

        assert stats.player_id == "2544"
        assert stats.player_name == "LeBron James"
        assert stats.points == 28
        assert stats.efficiency_rating == 1.15
        assert stats.true_shooting_percentage == 0.625
        assert stats.usage_rate == 0.28
        assert stats.plus_minus == 8
        assert stats.season == "2023-24"
        assert stats.partition_key is not None

    def test_minimal_gold_player_daily_stats(self):
        """Test creating Gold player daily stats with minimal required fields."""
        stats = GoldPlayerDailyStats(
            player_id="2544",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert stats.player_id == "2544"
        assert stats.points == 25
        assert stats.rebounds == 10
        assert stats.assists == 5
        # Optional Gold fields should be None
        assert stats.efficiency_rating is None
        assert stats.true_shooting_percentage is None
        assert stats.usage_rate is None
        assert stats.plus_minus is None

    def test_invalid_true_shooting_percentage(self):
        """Test validation of invalid true shooting percentage."""
        from pydantic import ValidationError

        with pytest.raises(
            ValidationError, match="Input should be less than or equal to 1"
        ):
            GoldPlayerDailyStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                true_shooting_percentage=1.5,  # Invalid - greater than 1
            )

        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            GoldPlayerDailyStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                true_shooting_percentage=-0.1,  # Invalid - negative
            )

    def test_invalid_season_format(self):
        """Test validation of invalid season format."""
        with pytest.raises(ValueError, match="Season must be in format 'YYYY-YY'"):
            GoldPlayerDailyStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                season="2023",  # Invalid format
            )

    def test_valid_season_formats(self):
        """Test valid season formats."""
        valid_seasons = ["2023-24", "2024-25", "2022-23"]

        for season in valid_seasons:
            stats = GoldPlayerDailyStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                season=season,
            )
            assert stats.season == season


class TestGoldPlayerSeasonSummary:
    """Test Gold layer player season summary model."""

    def test_valid_gold_player_season_summary(self):
        """Test creating valid Gold player season summary."""
        summary = GoldPlayerSeasonSummary(
            player_id="2544",
            player_name="LeBron James",
            season="2023-24",
            team="LAL",
            total_games=70,
            total_minutes=2520.5,
            points_per_game=27.8,
            rebounds_per_game=8.2,
            assists_per_game=6.8,
            steals_per_game=1.1,
            blocks_per_game=0.8,
            turnovers_per_game=3.2,
            field_goal_percentage=0.525,
            three_point_percentage=0.385,
            free_throw_percentage=0.745,
            efficiency_rating=1.25,
            true_shooting_percentage=0.615,
            usage_rate=0.285,
            scoring_trend=0.05,  # 5% increase
            efficiency_trend=-0.02,  # 2% decrease
            partition_key="season=2023-24/player_id=2544",
        )

        assert summary.player_id == "2544"
        assert summary.season == "2023-24"
        assert summary.total_games == 70
        assert summary.points_per_game == 27.8
        assert summary.efficiency_rating == 1.25
        assert summary.scoring_trend == 0.05
        assert summary.efficiency_trend == -0.02

    def test_minimal_season_summary(self):
        """Test creating season summary with minimal required fields."""
        summary = GoldPlayerSeasonSummary(
            player_id="2544",
            season="2023-24",
            total_games=70,
            total_minutes=2520.5,
            points_per_game=27.8,
            rebounds_per_game=8.2,
            assists_per_game=6.8,
            steals_per_game=1.1,
            blocks_per_game=0.8,
            turnovers_per_game=3.2,
        )

        assert summary.player_id == "2544"
        assert summary.season == "2023-24"
        # Optional fields should be None
        assert summary.efficiency_rating is None
        assert summary.scoring_trend is None

    def test_invalid_season_format_in_summary(self):
        """Test validation of invalid season format in summary."""
        with pytest.raises(ValueError, match="Season must be in format 'YYYY-YY'"):
            GoldPlayerSeasonSummary(
                player_id="2544",
                season="2023",  # Invalid format
                total_games=70,
                total_minutes=2520.5,
                points_per_game=27.8,
                rebounds_per_game=8.2,
                assists_per_game=6.8,
                steals_per_game=1.1,
                blocks_per_game=0.8,
                turnovers_per_game=3.2,
            )

    def test_negative_stats_validation(self):
        """Test validation of negative statistics."""
        with pytest.raises(ValueError):
            GoldPlayerSeasonSummary(
                player_id="2544",
                season="2023-24",
                total_games=-1,  # Invalid - negative
                total_minutes=2520.5,
                points_per_game=27.8,
                rebounds_per_game=8.2,
                assists_per_game=6.8,
                steals_per_game=1.1,
                blocks_per_game=0.8,
                turnovers_per_game=3.2,
            )


class TestGoldTeamDailyStats:
    """Test Gold layer team daily statistics model."""

    def test_valid_gold_team_daily_stats(self):
        """Test creating valid Gold team daily stats."""
        stats = GoldTeamDailyStats(
            team_id="1610612747",
            team_name="Los Angeles Lakers",
            game_id="0022300123",
            game_date="2024-01-15",
            season="2023-24",
            points=118,
            field_goals_made=45,
            field_goals_attempted=88,
            three_pointers_made=12,
            three_pointers_attempted=35,
            free_throws_made=16,
            free_throws_attempted=20,
            rebounds=46,
            assists=28,
            steals=8,
            blocks=5,
            turnovers=12,
            fouls=18,
            offensive_rating=115.2,
            defensive_rating=108.7,
            pace=98.5,
            true_shooting_percentage=0.615,
            opponent_team_id="1610612738",
            home_game=True,
            win=True,
            partition_key="season=2023-24/team_id=1610612747/date=2024-01-15",
        )

        assert stats.team_id == "1610612747"
        assert stats.team_name == "Los Angeles Lakers"
        assert stats.points == 118
        assert stats.offensive_rating == 115.2
        assert stats.defensive_rating == 108.7
        assert stats.pace == 98.5
        assert stats.home_game is True
        assert stats.win is True

    def test_minimal_team_daily_stats(self):
        """Test creating team daily stats with minimal required fields."""
        stats = GoldTeamDailyStats(
            team_id="1610612747",
            team_name="Los Angeles Lakers",
            points=118,
            field_goals_made=45,
            field_goals_attempted=88,
            rebounds=46,
            assists=28,
        )

        assert stats.team_id == "1610612747"
        assert stats.team_name == "Los Angeles Lakers"
        assert stats.points == 118
        # Optional Gold fields should be None
        assert stats.offensive_rating is None
        assert stats.defensive_rating is None
        assert stats.pace is None
        assert stats.home_game is None
        assert stats.win is None

    def test_team_name_validation(self):
        """Test team name validation."""
        from pydantic import ValidationError

        # Empty string should be caught by field validation
        with pytest.raises(ValidationError):
            GoldTeamDailyStats(
                team_id="1610612747",
                team_name="",  # Invalid - empty string
                points=118,
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )

    def test_negative_team_stats_validation(self):
        """Test validation of negative team statistics."""
        with pytest.raises(ValueError):
            GoldTeamDailyStats(
                team_id="1610612747",
                team_name="Los Angeles Lakers",
                points=-10,  # Invalid - negative
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )


class TestGoldModelIntegration:
    """Test integration aspects of Gold layer models."""

    def test_gold_model_serialization(self):
        """Test that Gold models can be serialized to dict."""
        stats = GoldPlayerDailyStats(
            player_id="2544",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            efficiency_rating=1.15,
            season="2023-24",
        )

        data_dict = stats.model_dump()

        assert data_dict["player_id"] == "2544"
        assert data_dict["points"] == 25
        assert data_dict["efficiency_rating"] == 1.15
        assert data_dict["season"] == "2023-24"
        assert "lineage" in data_dict

    def test_gold_model_from_dict(self):
        """Test creating Gold models from dictionary data."""
        data = {
            "player_id": "2544",
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "efficiency_rating": 1.15,
            "season": "2023-24",
        }

        stats = GoldPlayerDailyStats(**data)

        assert stats.player_id == "2544"
        assert stats.efficiency_rating == 1.15
        assert stats.season == "2023-24"

    def test_gold_model_backward_compatibility(self):
        """Test that Gold models maintain backward compatibility with Silver fields."""
        # Create with Silver-like data (no Gold-specific fields)
        stats = GoldPlayerDailyStats(
            player_id="2544",
            player_name="LeBron James",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            field_goals_made=10,
            field_goals_attempted=18,
            minutes_played=35.5,
            game_id="0022300123",
        )

        # Should work fine - Gold fields are optional
        assert stats.player_id == "2544"
        assert stats.player_name == "LeBron James"
        assert stats.points == 25
        # Gold-specific fields should be None
        assert stats.efficiency_rating is None
        assert stats.true_shooting_percentage is None
