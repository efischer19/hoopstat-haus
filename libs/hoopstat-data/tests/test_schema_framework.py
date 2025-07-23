"""
Tests for the enhanced Pydantic schema validation framework.

Tests the new features including:
- Schema versioning and evolution
- Validation strictness levels
- Data lineage tracking
- NBA-specific custom validators
- JSON schema generation
"""

from datetime import datetime

import pytest

from hoopstat_data.models import (
    DataLineage,
    GameStats,
    PlayerStats,
    SchemaEvolution,
    TeamStats,
    ValidationMode,
    generate_json_schema,
    get_schema_version,
)


class TestDataLineage:
    """Test data lineage tracking functionality."""

    def test_data_lineage_creation(self):
        """Test creating data lineage objects."""
        lineage = DataLineage(
            source_system="nba_api",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        assert lineage.source_system == "nba_api"
        assert lineage.schema_version == "1.0.0"
        assert lineage.transformation_stage == "silver"
        assert lineage.validation_mode == ValidationMode.STRICT
        assert isinstance(lineage.ingestion_timestamp, datetime)

    def test_data_lineage_defaults(self):
        """Test data lineage with default values."""
        lineage = DataLineage(
            source_system="test_system",
            schema_version="1.0.0",
            transformation_stage="bronze",
        )

        assert lineage.validation_mode == ValidationMode.STRICT
        assert isinstance(lineage.ingestion_timestamp, datetime)


class TestValidationModes:
    """Test strict vs lenient validation modes."""

    def test_strict_mode_field_goals_validation(self):
        """Test strict mode rejects invalid field goal ratios."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        with pytest.raises(
            ValueError, match="Field goals attempted must be >= field goals made"
        ):
            PlayerStats(
                lineage=lineage,
                player_id="test_player",
                points=25,
                rebounds=8,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=3,
                field_goals_made=15,
                field_goals_attempted=10,  # Invalid: less than made
            )

    def test_lenient_mode_allows_field_goals_inconsistency(self):
        """Test lenient mode allows field goal inconsistencies."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.LENIENT,
        )

        # This should not raise an exception in lenient mode
        player = PlayerStats(
            lineage=lineage,
            player_id="test_player",
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
            field_goals_made=15,
            field_goals_attempted=10,  # Invalid but allowed in lenient mode
        )

        assert player.field_goals_made == 15
        assert player.field_goals_attempted == 10

    def test_strict_mode_rejects_high_points(self):
        """Test strict mode rejects unreasonably high points."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        with pytest.raises(
            ValueError, match="Points exceeds reasonable NBA single-game maximum"
        ):
            PlayerStats(
                lineage=lineage,
                player_id="test_player",
                points=150,  # Unreasonably high
                rebounds=8,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=3,
            )

    def test_strict_mode_rejects_tied_games(self):
        """Test strict mode rejects tied NBA games."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        with pytest.raises(ValueError, match="NBA games cannot end in ties"):
            GameStats(
                lineage=lineage,
                game_id="test_game",
                home_team_id="lakers",
                away_team_id="celtics",
                home_score=100,
                away_score=100,  # Tied game
            )

    def test_lenient_mode_allows_tied_games(self):
        """Test lenient mode allows tied games."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.LENIENT,
        )

        # Should not raise exception in lenient mode
        game = GameStats(
            lineage=lineage,
            game_id="test_game",
            home_team_id="lakers",
            away_team_id="celtics",
            home_score=100,
            away_score=100,  # Tied game allowed in lenient mode
        )

        assert game.home_score == 100
        assert game.away_score == 100


class TestNBASpecificValidators:
    """Test NBA-specific business rule validators."""

    def test_player_name_validation(self):
        """Test player name cannot be empty string."""
        with pytest.raises(ValueError, match="Player name cannot be empty string"):
            PlayerStats(
                player_id="test_player",
                player_name="   ",  # Empty after strip
                points=25,
                rebounds=8,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=3,
            )

    def test_team_name_validation(self):
        """Test team name validation."""
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            TeamStats(
                team_id="test_team",
                team_name="",  # Empty team name
                points=110,
                field_goals_made=40,
                field_goals_attempted=85,
                rebounds=45,
                assists=25,
            )

    def test_season_format_validation(self):
        """Test NBA season format validation."""
        # Valid season format should work
        game = GameStats(
            game_id="test_game",
            home_team_id="lakers",
            away_team_id="celtics",
            home_score=110,
            away_score=105,
            season="2023-24",  # Valid format
        )

        assert game.season == "2023-24"

    def test_game_date_validation(self):
        """Test game date ISO format validation."""
        with pytest.raises(ValueError, match="Game date must be in ISO format"):
            GameStats(
                game_id="test_game",
                home_team_id="lakers",
                away_team_id="celtics",
                home_score=110,
                away_score=105,
                game_date="2024/01/15",  # Invalid format
            )

    def test_same_team_validation(self):
        """Test teams cannot play themselves."""
        with pytest.raises(ValueError, match="Home and away teams cannot be the same"):
            GameStats(
                game_id="test_game",
                home_team_id="lakers",
                away_team_id="lakers",  # Same team
                home_score=110,
                away_score=105,
            )

    def test_overtime_quarters_validation(self):
        """Test overtime games must have correct quarters."""
        lineage = DataLineage(
            source_system="test",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        with pytest.raises(
            ValueError, match="Overtime games must have at least 5 quarters"
        ):
            GameStats(
                lineage=lineage,
                game_id="test_game",
                home_team_id="lakers",
                away_team_id="celtics",
                home_score=110,
                away_score=105,
                overtime=True,
                quarters=4,  # Should be 5+ for overtime
            )


class TestSchemaGeneration:
    """Test JSON schema generation functionality."""

    def test_generate_player_stats_schema(self):
        """Test generating JSON schema for PlayerStats."""
        schema = generate_json_schema(PlayerStats)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Check required fields
        required_fields = schema["required"]
        assert "player_id" in required_fields
        assert "points" in required_fields
        assert "rebounds" in required_fields
        assert "assists" in required_fields

        # Check property definitions
        properties = schema["properties"]
        assert "player_id" in properties
        assert "lineage" in properties
        assert properties["points"]["minimum"] == 0

    def test_generate_team_stats_schema(self):
        """Test generating JSON schema for TeamStats."""
        schema = generate_json_schema(TeamStats)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        properties = schema["properties"]
        assert "team_id" in properties
        assert "team_name" in properties
        assert "lineage" in properties

    def test_generate_game_stats_schema(self):
        """Test generating JSON schema for GameStats."""
        schema = generate_json_schema(GameStats)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        properties = schema["properties"]
        assert "game_id" in properties
        assert "home_team_id" in properties
        assert "away_team_id" in properties
        assert "lineage" in properties


class TestSchemaVersioning:
    """Test schema versioning and evolution."""

    def test_get_current_schema_version(self):
        """Test getting current schema version."""
        version = get_schema_version()
        assert isinstance(version, str)
        assert "." in version  # Should be in semver format

    def test_schema_evolution_no_change(self):
        """Test schema evolution with same version."""
        data = {"player_id": "test", "points": 25}
        result = SchemaEvolution.migrate_from_version(data, "1.0.0", "1.0.0")

        assert result == data

    def test_schema_evolution_migration(self):
        """Test schema evolution migration from older version."""
        data = {"player_id": "test", "points": 25}
        result = SchemaEvolution.migrate_from_version(data, "0.1.0", "1.0.0")

        # Should add lineage data
        assert "lineage" in result
        assert result["lineage"]["source_system"] == "unknown"
        assert result["lineage"]["schema_version"] == "1.0.0"


class TestBaseSilverModel:
    """Test BaseSilverModel functionality."""

    def test_default_lineage_creation(self):
        """Test that default lineage is created when not provided."""
        player = PlayerStats(
            player_id="test_player",
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert player.lineage is not None
        assert player.lineage.source_system == "unknown"
        assert player.lineage.schema_version == get_schema_version()
        assert player.lineage.transformation_stage == "silver"
        assert player.lineage.validation_mode == ValidationMode.STRICT

    def test_custom_lineage_provided(self):
        """Test using custom lineage data."""
        custom_lineage = DataLineage(
            source_system="custom_api",
            schema_version="1.0.0",
            transformation_stage="gold",
            validation_mode=ValidationMode.LENIENT,
        )

        player = PlayerStats(
            lineage=custom_lineage,
            player_id="test_player",
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert player.lineage.source_system == "custom_api"
        assert player.lineage.transformation_stage == "gold"
        assert player.lineage.validation_mode == ValidationMode.LENIENT

    def test_validation_mode_in_constructor(self):
        """Test passing validation mode in constructor."""
        player = PlayerStats(
            validation_mode=ValidationMode.LENIENT,
            player_id="test_player",
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert player.lineage.validation_mode == ValidationMode.LENIENT


class TestPerformanceAndErrorMessages:
    """Test performance optimizations and error messaging."""

    def test_comprehensive_error_messages(self):
        """Test that validation errors provide comprehensive messages."""
        try:
            PlayerStats(
                player_id="test_player",
                points=25,
                rebounds=8,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=3,
                field_goals_made=15,
                field_goals_attempted=10,  # Invalid
            )
        except ValueError as e:
            assert "Field goals attempted must be >= field goals made" in str(e)

    def test_model_config_settings(self):
        """Test that model configuration is applied correctly."""
        player = PlayerStats(
            player_id="  test_player  ",  # Should be stripped
            player_name="  LeBron James  ",  # Should be stripped
            points=25,
            rebounds=8,
            assists=7,
            steals=2,
            blocks=1,
            turnovers=3,
        )

        assert player.player_id == "test_player"
        assert player.player_name == "LeBron James"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValueError):
            PlayerStats(
                player_id="test_player",
                points=25,
                rebounds=8,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=3,
                unknown_field="should_fail",  # Extra field should be rejected
            )
