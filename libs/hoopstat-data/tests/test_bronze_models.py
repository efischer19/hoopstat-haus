"""Tests for Bronze layer data models."""

from hoopstat_data.bronze_models import (
    BoxScoreRaw,
    PlayByPlayRaw,
    PlayerRaw,
    PlayerStatsRaw,
    ScheduleGameRaw,
    TeamRaw,
    TeamStatsRaw,
    generate_all_bronze_schemas,
    generate_bronze_json_schema,
)
from hoopstat_data.models import ValidationMode


class TestTeamRaw:
    """Test cases for TeamRaw Bronze model."""

    def test_valid_team_raw(self):
        """Test creating valid team from mock data structure."""
        team_data = {
            "id": 1,
            "name": "Celtics",
            "city": "Boston",
            "full_name": "Boston Celtics",
            "abbreviation": "BOS",
            "conference": "Eastern",
            "division": "Atlantic",
        }

        team = TeamRaw(**team_data)

        assert team.id == 1
        assert team.name == "Celtics"
        assert team.city == "Boston"
        assert team.full_name == "Boston Celtics"
        assert team.abbreviation == "BOS"
        assert team.conference == "Eastern"
        assert team.division == "Atlantic"
        assert team.lineage.transformation_stage == "bronze"
        assert team.lineage.validation_mode == ValidationMode.LENIENT

    def test_minimal_team_raw(self):
        """Test team with only required ID field."""
        team = TeamRaw(id=1)

        assert team.id == 1
        assert team.name is None
        assert team.city is None
        assert team.lineage.transformation_stage == "bronze"

    def test_team_raw_extra_fields_allowed(self):
        """Test that Bronze layer allows extra fields from API."""
        team_data = {
            "id": 1,
            "name": "Lakers",
            "city": "Los Angeles",
            "unknown_field": "some_value",  # Extra field should be allowed
            "api_specific_data": {"nested": "value"},
        }

        team = TeamRaw(**team_data)

        assert team.id == 1
        assert team.name == "Lakers"
        # Extra fields should not cause validation error


class TestPlayerRaw:
    """Test cases for PlayerRaw Bronze model."""

    def test_valid_player_raw(self):
        """Test creating valid player from mock data structure."""
        player_data = {
            "id": 1,
            "first_name": "Anthony",
            "last_name": "Miller",
            "full_name": "Anthony Miller",
            "team_id": 1,
            "position": "C",
            "jersey_number": 87,
            "height_inches": 81,
            "weight_pounds": 240,
            "age": 20,
            "years_experience": 0,
        }

        player = PlayerRaw(**player_data)

        assert player.id == 1
        assert player.first_name == "Anthony"
        assert player.last_name == "Miller"
        assert player.full_name == "Anthony Miller"
        assert player.team_id == 1
        assert player.position == "C"
        assert player.jersey_number == 87
        assert player.height_inches == 81
        assert player.weight_pounds == 240
        assert player.age == 20
        assert player.years_experience == 0
        assert player.lineage.transformation_stage == "bronze"

    def test_minimal_player_raw(self):
        """Test player with only required ID field."""
        player = PlayerRaw(id=2)

        assert player.id == 2
        assert player.first_name is None
        assert player.team_id is None

    def test_player_raw_invalid_data_lenient(self):
        """Test that Bronze layer accepts questionable data leniently."""
        # Data that might be problematic but should be accepted in Bronze
        player_data = {
            "id": 1,
            "height_inches": -1,  # Negative height - should be accepted in Bronze
            "age": 150,  # Unrealistic age - should be accepted in Bronze
            "jersey_number": 999,  # Invalid jersey number - should be accepted
        }

        player = PlayerRaw(**player_data)

        assert player.id == 1
        assert player.height_inches == -1  # Accepted despite being invalid
        assert player.age == 150  # Accepted despite being unrealistic


class TestScheduleGameRaw:
    """Test cases for ScheduleGameRaw Bronze model."""

    def test_valid_game_raw(self):
        """Test creating valid game from mock data structure."""
        game_data = {
            "id": 1,
            "season": "2023-24",
            "game_date": "2023-11-06 22:30:00",
            "home_team_id": 1,
            "away_team_id": 2,
            "home_score": 92,
            "away_score": 109,
            "game_type": "Regular Season",
            "is_completed": True,
        }

        game = ScheduleGameRaw(**game_data)

        assert game.id == 1
        assert game.season == "2023-24"
        assert game.game_date == "2023-11-06 22:30:00"
        assert game.home_team_id == 1
        assert game.away_team_id == 2
        assert game.home_score == 92
        assert game.away_score == 109
        assert game.game_type == "Regular Season"
        assert game.is_completed is True

    def test_incomplete_game_raw(self):
        """Test game with null scores (incomplete game)."""
        game_data = {
            "id": 2,
            "season": "2023-24",
            "game_date": "2023-11-24 20:30:00",
            "home_team_id": 3,
            "away_team_id": 1,
            "home_score": None,  # Incomplete game
            "away_score": None,
            "game_type": "Regular Season",
            "is_completed": False,
        }

        game = ScheduleGameRaw(**game_data)

        assert game.id == 2
        assert game.home_score is None
        assert game.away_score is None
        assert game.is_completed is False


class TestPlayerStatsRaw:
    """Test cases for PlayerStatsRaw Bronze model."""

    def test_valid_player_stats_raw(self):
        """Test creating valid player stats from mock data."""
        stats_data = {
            "player_id": 2,
            "game_id": 1,
            "team_id": 1,
            "minutes_played": 32.7,
            "points": 12,
            "rebounds": 1,
            "assists": 2,
            "steals": 2,
            "blocks": 2,
            "turnovers": 1,
            "fouls": 2,
            "field_goals_made": 2,
            "field_goals_attempted": 5,
            "three_pointers_made": 0,
            "three_pointers_attempted": 2,
            "free_throws_made": 1,
            "free_throws_attempted": 2,
        }

        stats = PlayerStatsRaw(**stats_data)

        assert stats.player_id == 2
        assert stats.game_id == 1
        assert stats.team_id == 1
        assert stats.minutes_played == 32.7
        assert stats.points == 12
        assert stats.rebounds == 1
        assert stats.field_goals_made == 2
        assert stats.field_goals_attempted == 5

    def test_player_stats_raw_string_minutes(self):
        """Test that Bronze accepts minutes as string (API variation)."""
        stats_data = {
            "player_id": 2,
            "minutes_played": "32:42",  # String format from some APIs
            "points": 12,
        }

        stats = PlayerStatsRaw(**stats_data)

        assert stats.player_id == 2
        assert stats.minutes_played == "32:42"  # Accepted as string
        assert stats.points == 12

    def test_player_stats_raw_inconsistent_data(self):
        """Test that Bronze accepts statistically inconsistent data."""
        stats_data = {
            "player_id": 1,
            "field_goals_made": 10,
            "field_goals_attempted": 5,  # Less than made - should be accepted in Bronze
            "points": 200,  # Unrealistic - should be accepted in Bronze
        }

        stats = PlayerStatsRaw(**stats_data)

        assert stats.field_goals_made == 10
        assert stats.field_goals_attempted == 5  # Inconsistent but accepted
        assert stats.points == 200  # Unrealistic but accepted


class TestTeamStatsRaw:
    """Test cases for TeamStatsRaw Bronze model."""

    def test_valid_team_stats_raw(self):
        """Test creating valid team stats from mock data."""
        stats_data = {
            "team_id": 1,
            "game_id": 1,
            "points": 76,
            "rebounds": 26,
            "assists": 13,
            "steals": 6,
            "blocks": 5,
            "turnovers": 15,
            "fouls": 19,
            "field_goals_made": 9,
            "field_goals_attempted": 30,
            "three_pointers_made": 0,
            "three_pointers_attempted": 5,
            "free_throws_made": 11,
            "free_throws_attempted": 22,
        }

        stats = TeamStatsRaw(**stats_data)

        assert stats.team_id == 1
        assert stats.game_id == 1
        assert stats.points == 76
        assert stats.rebounds == 26
        assert stats.assists == 13
        assert stats.field_goals_made == 9
        assert stats.field_goals_attempted == 30


class TestPlayByPlayRaw:
    """Test cases for PlayByPlayRaw Bronze model."""

    def test_valid_play_by_play_raw(self):
        """Test creating valid play-by-play entry."""
        play_data = {
            "game_id": 1,
            "event_id": 1,
            "event_num": 1,
            "period": 1,
            "time_remaining": "11:42",
            "event_type": "Made Shot",
            "action_type": "2-pt",
            "description": "Player makes 2-pt shot",
            "player1_id": 1,
            "player1_name": "John Doe",
            "player1_team_id": 1,
            "home_score": 2,
            "away_score": 0,
            "location_x": 25.0,
            "location_y": 10.0,
            "shot_distance": 15.5,
        }

        play = PlayByPlayRaw(**play_data)

        assert play.game_id == 1
        assert play.event_id == 1
        assert play.period == 1
        assert play.time_remaining == "11:42"
        assert play.event_type == "Made Shot"
        assert play.player1_id == 1
        assert play.home_score == 2
        assert play.shot_distance == 15.5

    def test_minimal_play_by_play(self):
        """Test play-by-play with minimal data."""
        play = PlayByPlayRaw(game_id=1)

        assert play.game_id == 1
        assert play.event_id is None
        assert play.player1_id is None


class TestBoxScoreRaw:
    """Test cases for BoxScoreRaw Bronze model."""

    def test_valid_box_score_raw(self):
        """Test creating valid boxscore container."""
        home_team = TeamRaw(id=1, name="Lakers")
        away_team = TeamRaw(id=2, name="Celtics")

        home_stats = TeamStatsRaw(team_id=1, points=110)
        away_stats = TeamStatsRaw(team_id=2, points=105)

        player_stats = [
            PlayerStatsRaw(player_id=1, points=25),
            PlayerStatsRaw(player_id=2, points=20),
        ]

        boxscore_data = {
            "game_id": 1,
            "game_date": "2024-01-15",
            "home_team": home_team,
            "away_team": away_team,
            "home_team_stats": home_stats,
            "away_team_stats": away_stats,
            "home_players": player_stats,
            "away_players": [],
            "officials": ["Referee 1", "Referee 2"],
            "arena": "Crypto.com Arena",
            "attendance": 20000,
        }

        boxscore = BoxScoreRaw(**boxscore_data)

        assert boxscore.game_id == 1
        assert boxscore.game_date == "2024-01-15"
        assert boxscore.home_team.name == "Lakers"
        assert boxscore.away_team.name == "Celtics"
        assert boxscore.home_team_stats.points == 110
        assert len(boxscore.home_players) == 2
        assert boxscore.arena == "Crypto.com Arena"
        assert boxscore.attendance == 20000

    def test_minimal_box_score(self):
        """Test boxscore with minimal data."""
        boxscore = BoxScoreRaw(game_id=1)

        assert boxscore.game_id == 1
        assert boxscore.home_team is None
        assert boxscore.home_players is None


class TestBronzeSchemaGeneration:
    """Test schema generation for Bronze models."""

    def test_generate_bronze_json_schema(self):
        """Test generating JSON schema for a Bronze model."""
        schema = generate_bronze_json_schema(TeamRaw)

        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]

    def test_generate_all_bronze_schemas(self):
        """Test generating all Bronze schemas."""
        schemas = generate_all_bronze_schemas()

        assert isinstance(schemas, dict)
        assert "TeamRaw" in schemas
        assert "PlayerRaw" in schemas
        assert "ScheduleGameRaw" in schemas
        assert "PlayerStatsRaw" in schemas
        assert "TeamStatsRaw" in schemas
        assert "PlayByPlayRaw" in schemas
        assert "BoxScoreRaw" in schemas

        # Check that each schema is a valid JSON schema dict
        for _model_name, schema in schemas.items():
            assert isinstance(schema, dict)
            assert "type" in schema
            assert "properties" in schema


class TestBronzeValidationMode:
    """Test validation mode behavior in Bronze models."""

    def test_bronze_default_validation_mode(self):
        """Test that Bronze models default to lenient validation."""
        team = TeamRaw(id=1)

        assert team.lineage.validation_mode == ValidationMode.LENIENT
        assert team.lineage.transformation_stage == "bronze"
        assert team.lineage.source_system == "nba-api"

    def test_bronze_extra_fields_allowed(self):
        """Test that Bronze models allow extra fields."""
        # This should not raise an error even with unknown fields
        team_data = {
            "id": 1,
            "name": "Lakers",
            "unknown_api_field": "value",
            "nested_data": {"key": "value"},
            "random_number": 42,
        }

        team = TeamRaw(**team_data)

        assert team.id == 1
        assert team.name == "Lakers"
        # Should not raise validation error for extra fields

    def test_bronze_accepts_invalid_data_types(self):
        """Test that Bronze is more lenient with data types where possible."""
        # Test that some fields can accept various data types
        stats_data = {
            "player_id": 1,
            "minutes_played": "32:42",  # String instead of float
            "points": 25,
        }

        stats = PlayerStatsRaw(**stats_data)

        assert stats.player_id == 1
        assert stats.minutes_played == "32:42"  # Accepted as string
        assert stats.points == 25
