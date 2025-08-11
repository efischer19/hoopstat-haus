"""Tests for Silver layer data models."""

import pytest
from pydantic import ValidationError

from hoopstat_data.silver_models import (
    DataLineage,
    GameStats,
    PlayerStats,
    TeamStats,
    ValidationMode,
    generate_all_silver_schemas,
    generate_silver_json_schema,
)


class TestBaseSilverModel:
    """Test cases for BaseSilverModel base class."""

    def test_silver_model_lineage_creation(self):
        """Test that Silver models automatically set transformation stage."""
        # Create a concrete Silver model instance
        stats = PlayerStats(
            player_id="test_player",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert stats.lineage is not None
        assert stats.lineage.transformation_stage == "silver"
        assert stats.lineage.validation_mode == ValidationMode.STRICT
        assert stats.lineage.source_system == "unknown"

    def test_silver_model_with_existing_lineage(self):
        """Test Silver model with provided lineage preserves lineage values."""
        lineage = DataLineage(
            source_system="bronze-to-silver-etl",
            schema_version="1.0.0",
            transformation_stage="bronze",  # Preserved as-is in Silver models
            validation_mode=ValidationMode.STRICT,
        )

        stats = PlayerStats(
            player_id="test_player",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            lineage=lineage,
        )

        # Silver models preserve existing lineage values (unlike Gold models)
        assert stats.lineage.transformation_stage == "bronze"
        assert stats.lineage.source_system == "bronze-to-silver-etl"

    def test_silver_model_forbids_extra_fields(self):
        """Test that Silver models forbid extra fields (strict validation)."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            PlayerStats(
                player_id="test_player",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                unknown_field="should_fail",  # Extra field not allowed in Silver
            )


class TestPlayerStats:
    """Test cases for PlayerStats Silver model."""

    def test_valid_player_stats_silver(self):
        """Test creating valid player stats with strict validation."""
        stats = PlayerStats(
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
        )

        assert stats.player_id == "2544"
        assert stats.player_name == "LeBron James"
        assert stats.team == "LAL"
        assert stats.position == "SF"
        assert stats.points == 28
        assert stats.rebounds == 8
        assert stats.assists == 7
        assert stats.field_goals_made == 10
        assert stats.field_goals_attempted == 20
        assert stats.lineage.transformation_stage == "silver"
        assert stats.lineage.validation_mode == ValidationMode.STRICT

    def test_minimal_player_stats_silver(self):
        """Test player stats with only required fields."""
        stats = PlayerStats(
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
        assert stats.player_name is None
        assert stats.team is None
        assert stats.field_goals_made is None

    def test_negative_stats_rejected_silver(self):
        """Test that Silver layer strictly rejects negative stats."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            PlayerStats(
                player_id="2544",
                points=-5,  # Negative points rejected in Silver
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
            )

        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            PlayerStats(
                player_id="2544",
                points=25,
                rebounds=-1,  # Negative rebounds rejected in Silver
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
            )

    def test_field_goals_consistency_strict(self):
        """Test that Silver layer strictly validates field goal consistency."""
        with pytest.raises(
            ValidationError, match="Field goals attempted must be >= field goals made"
        ):
            PlayerStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                field_goals_made=15,
                field_goals_attempted=10,  # Less than made - rejected in Silver
            )

    def test_unrealistic_points_strict_validation(self):
        """Test that Silver layer validates unrealistic point totals."""
        with pytest.raises(
            ValidationError, match="Points exceeds reasonable NBA single-game maximum"
        ):
            PlayerStats(
                player_id="2544",
                points=150,  # Unrealistic points rejected in Silver
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
            )

    def test_empty_player_name_rejected(self):
        """Test that empty player names are rejected in Silver."""
        with pytest.raises(ValidationError, match="Player name cannot be empty string"):
            PlayerStats(
                player_id="2544",
                player_name="   ",  # Empty/whitespace name rejected
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
            )

    def test_shooting_stats_consistency_validation(self):
        """Test comprehensive shooting statistics validation in Silver."""
        with pytest.raises(ValidationError):
            PlayerStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                three_pointers_made=5,
                three_pointers_attempted=3,  # Inconsistent 3PT stats
            )

        with pytest.raises(ValidationError):
            PlayerStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                free_throws_made=8,
                free_throws_attempted=6,  # Inconsistent FT stats
            )


class TestTeamStats:
    """Test cases for TeamStats Silver model."""

    def test_valid_team_stats_silver(self):
        """Test creating valid team stats with strict validation."""
        stats = TeamStats(
            team_id="1610612747",
            team_name="Los Angeles Lakers",
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
            game_id="0022300123",
        )

        assert stats.team_id == "1610612747"
        assert stats.team_name == "Los Angeles Lakers"
        assert stats.points == 118
        assert stats.field_goals_made == 45
        assert stats.field_goals_attempted == 88
        assert stats.rebounds == 46
        assert stats.assists == 28
        assert stats.lineage.transformation_stage == "silver"

    def test_minimal_team_stats_silver(self):
        """Test team stats with only required fields."""
        stats = TeamStats(
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
        assert stats.steals is None
        assert stats.blocks is None

    def test_empty_team_name_rejected(self):
        """Test that empty team names are rejected in Silver."""
        with pytest.raises(ValidationError, match="Team name cannot be empty"):
            TeamStats(
                team_id="1610612747",
                team_name="",  # Empty team name rejected
                points=118,
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )

        with pytest.raises(ValidationError, match="Team name cannot be empty"):
            TeamStats(
                team_id="1610612747",
                team_name="   ",  # Whitespace team name rejected
                points=118,
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )

    def test_unrealistic_team_points_validation(self):
        """Test validation of unrealistic team point totals."""
        with pytest.raises(
            ValidationError,
            match="Team points exceed reasonable NBA single-game maximum",
        ):
            TeamStats(
                team_id="1610612747",
                team_name="Los Angeles Lakers",
                points=250,  # Unrealistic high score rejected
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )

        with pytest.raises(
            ValidationError,
            match="Team points below reasonable NBA single-game minimum",
        ):
            TeamStats(
                team_id="1610612747",
                team_name="Los Angeles Lakers",
                points=50,  # Unrealistic low score rejected
                field_goals_made=45,
                field_goals_attempted=88,
                rebounds=46,
                assists=28,
            )

    def test_team_shooting_consistency_validation(self):
        """Test team shooting statistics consistency validation."""
        with pytest.raises(
            ValidationError,
            match="Field goals made cannot exceed field goals attempted",
        ):
            TeamStats(
                team_id="1610612747",
                team_name="Los Angeles Lakers",
                points=118,
                field_goals_made=50,
                field_goals_attempted=45,  # Inconsistent FG stats
                rebounds=46,
                assists=28,
            )

        with pytest.raises(
            ValidationError,
            match="Three pointers made cannot exceed three pointers attempted",
        ):
            TeamStats(
                team_id="1610612747",
                team_name="Los Angeles Lakers",
                points=118,
                field_goals_made=45,
                field_goals_attempted=88,
                three_pointers_made=20,
                three_pointers_attempted=15,  # Inconsistent 3PT stats
                rebounds=46,
                assists=28,
            )


class TestGameStats:
    """Test cases for GameStats Silver model."""

    def test_valid_game_stats_silver(self):
        """Test creating valid game stats with strict validation."""
        stats = GameStats(
            game_id="0022300123",
            home_team_id="1610612747",
            away_team_id="1610612738",
            home_score=118,
            away_score=112,
            season="2023-24",
            game_date="2024-01-15T20:00:00Z",
            venue="Crypto.com Arena",
            quarters=4,
            overtime=False,
        )

        assert stats.game_id == "0022300123"
        assert stats.home_team_id == "1610612747"
        assert stats.away_team_id == "1610612738"
        assert stats.home_score == 118
        assert stats.away_score == 112
        assert stats.season == "2023-24"
        assert stats.game_date == "2024-01-15T20:00:00Z"
        assert stats.venue == "Crypto.com Arena"
        assert stats.quarters == 4
        assert stats.overtime is False
        assert stats.lineage.transformation_stage == "silver"

    def test_minimal_game_stats_silver(self):
        """Test game stats with only required fields."""
        stats = GameStats(
            game_id="0022300123",
            home_team_id="1610612747",
            away_team_id="1610612738",
            home_score=118,
            away_score=112,
        )

        assert stats.game_id == "0022300123"
        assert stats.home_team_id == "1610612747"
        assert stats.away_team_id == "1610612738"
        assert stats.home_score == 118
        assert stats.away_score == 112
        assert stats.season is None
        assert stats.game_date is None

    def test_same_team_validation(self):
        """Test that teams cannot play themselves."""
        with pytest.raises(
            ValidationError, match="Home and away teams cannot be the same"
        ):
            GameStats(
                game_id="0022300123",
                home_team_id="1610612747",
                away_team_id="1610612747",  # Same team - rejected
                home_score=118,
                away_score=112,
            )

    def test_tie_game_validation_strict(self):
        """Test that tie games are rejected in strict Silver validation."""
        with pytest.raises(ValidationError, match="NBA games cannot end in ties"):
            GameStats(
                game_id="0022300123",
                home_team_id="1610612747",
                away_team_id="1610612738",
                home_score=112,
                away_score=112,  # Tie game - rejected in strict mode
            )

    def test_invalid_game_date_format(self):
        """Test that invalid game date formats are rejected."""
        with pytest.raises(ValidationError, match="Game date must be in ISO format"):
            GameStats(
                game_id="0022300123",
                home_team_id="1610612747",
                away_team_id="1610612738",
                home_score=118,
                away_score=112,
                game_date="2024/01/15",  # Invalid date format
            )

    def test_overtime_quarters_validation(self):
        """Test overtime and quarters consistency validation."""
        with pytest.raises(
            ValidationError, match="Overtime games must have at least 5 quarters"
        ):
            GameStats(
                game_id="0022300123",
                home_team_id="1610612747",
                away_team_id="1610612738",
                home_score=118,
                away_score=112,
                quarters=4,
                overtime=True,  # Overtime but only 4 quarters - inconsistent
            )

    def test_valid_overtime_game(self):
        """Test valid overtime game configuration."""
        stats = GameStats(
            game_id="0022300123",
            home_team_id="1610612747",
            away_team_id="1610612738",
            home_score=128,
            away_score=125,
            quarters=5,
            overtime=True,
        )

        assert stats.quarters == 5
        assert stats.overtime is True

    def test_negative_scores_rejected(self):
        """Test that negative scores are rejected."""
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            GameStats(
                game_id="0022300123",
                home_team_id="1610612747",
                away_team_id="1610612738",
                home_score=-5,  # Negative score rejected
                away_score=112,
            )


class TestSilverSchemaGeneration:
    """Test schema generation for Silver models."""

    def test_generate_silver_json_schema(self):
        """Test generating JSON schema for a Silver model."""
        schema = generate_silver_json_schema(PlayerStats)

        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "player_id" in schema["properties"]
        assert "points" in schema["properties"]
        assert "lineage" in schema["properties"]

    def test_generate_all_silver_schemas(self):
        """Test generating all Silver schemas."""
        schemas = generate_all_silver_schemas()

        assert isinstance(schemas, dict)
        assert "PlayerStats" in schemas
        assert "TeamStats" in schemas
        assert "GameStats" in schemas

        # Check that each schema is a valid JSON schema dict
        for _model_name, schema in schemas.items():
            assert isinstance(schema, dict)
            assert "type" in schema
            assert "properties" in schema

        # Verify specific model schemas
        player_schema = schemas["PlayerStats"]
        assert "player_id" in player_schema["properties"]
        assert "points" in player_schema["properties"]

        team_schema = schemas["TeamStats"]
        assert "team_id" in team_schema["properties"]
        assert "team_name" in team_schema["properties"]

        game_schema = schemas["GameStats"]
        assert "game_id" in game_schema["properties"]
        assert "home_team_id" in game_schema["properties"]


class TestSilverValidationMode:
    """Test validation mode behavior in Silver models."""

    def test_silver_default_validation_mode(self):
        """Test that Silver models default to strict validation."""
        stats = PlayerStats(
            player_id="2544",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert stats.lineage.validation_mode == ValidationMode.STRICT
        assert stats.lineage.transformation_stage == "silver"

    def test_silver_lenient_mode_behavior(self):
        """Test Silver model behavior with lenient validation mode."""
        # Create lineage with lenient mode
        lenient_lineage = DataLineage(
            source_system="test-system",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.LENIENT,
        )

        # This should work in lenient mode (inconsistent field goals)
        stats = PlayerStats(
            player_id="2544",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
            field_goals_made=15,
            field_goals_attempted=10,  # Inconsistent but allowed in lenient mode
            lineage=lenient_lineage,
        )

        assert stats.field_goals_made == 15
        assert stats.field_goals_attempted == 10
        assert stats.lineage.validation_mode == ValidationMode.LENIENT

    def test_silver_strict_mode_enforcement(self):
        """Test that Silver models enforce strict validation by default."""
        # Default strict mode should reject inconsistent data
        with pytest.raises(ValidationError):
            PlayerStats(
                player_id="2544",
                points=25,
                rebounds=10,
                assists=5,
                steals=2,
                blocks=1,
                turnovers=3,
                field_goals_made=15,
                field_goals_attempted=10,  # Inconsistent - rejected in strict mode
            )


class TestSilverModelIntegration:
    """Test integration aspects of Silver layer models."""

    def test_silver_model_serialization(self):
        """Test that Silver models can be serialized to dict."""
        stats = PlayerStats(
            player_id="2544",
            player_name="LeBron James",
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        data_dict = stats.model_dump()

        assert data_dict["player_id"] == "2544"
        assert data_dict["player_name"] == "LeBron James"
        assert data_dict["points"] == 25
        assert "lineage" in data_dict
        assert data_dict["lineage"]["transformation_stage"] == "silver"

    def test_silver_model_from_dict(self):
        """Test creating Silver models from dictionary data."""
        data = {
            "player_id": "2544",
            "player_name": "LeBron James",
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
        }

        stats = PlayerStats(**data)

        assert stats.player_id == "2544"
        assert stats.player_name == "LeBron James"
        assert stats.points == 25
        assert stats.lineage.transformation_stage == "silver"

    def test_silver_to_gold_transformation_ready(self):
        """Test that Silver models are ready for Gold layer transformation."""
        # Silver model with clean, validated data
        silver_stats = PlayerStats(
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
        )

        # Should have all data needed for Gold transformation
        assert silver_stats.player_id is not None
        assert silver_stats.points >= 0
        assert silver_stats.field_goals_made <= silver_stats.field_goals_attempted
        assert silver_stats.lineage.transformation_stage == "silver"
        assert silver_stats.lineage.validation_mode == ValidationMode.STRICT

    def test_silver_whitespace_stripping(self):
        """Test that Silver models strip whitespace from string fields."""
        stats = PlayerStats(
            player_id="  2544  ",  # Should be stripped
            player_name="  LeBron James  ",  # Should be stripped
            team="  LAL  ",  # Should be stripped
            points=25,
            rebounds=10,
            assists=5,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert stats.player_id == "2544"
        assert stats.player_name == "LeBron James"
        assert stats.team == "LAL"
