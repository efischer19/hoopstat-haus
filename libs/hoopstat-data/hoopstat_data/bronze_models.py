"""
Bronze layer data models for raw NBA API payloads.

These models provide minimal transformation and lenient validation
for data ingestion from the nba_api library and other raw sources.
"""

from typing import Any

from pydantic import BaseModel, Field

from .silver_models import DataLineage, ValidationMode, get_schema_version


class BaseBronzeModel(BaseModel):
    """Base model for all Bronze layer entities with lenient validation."""

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": False,  # Lenient for Bronze
        "use_enum_values": True,
        "extra": "allow",  # Allow extra fields for raw API data
    }

    # Data lineage - optional with default for backward compatibility
    lineage: DataLineage | None = Field(
        None, description="Data lineage and metadata tracking"
    )

    def __init__(self, **data):
        """Initialize with lenient validation mode for Bronze layer."""
        # Provide default lineage if not supplied
        if "lineage" not in data:
            data["lineage"] = DataLineage(
                source_system="nba-api",
                schema_version=get_schema_version(),
                transformation_stage="bronze",
                validation_mode=ValidationMode.LENIENT,
            )
        super().__init__(**data)


class TeamRaw(BaseBronzeModel):
    """Raw team data model matching NBA API team endpoints."""

    # Core identifiers
    id: int = Field(..., description="NBA team ID")
    name: str | None = Field(None, description="Team name (e.g., 'Lakers')")
    city: str | None = Field(None, description="Team city (e.g., 'Los Angeles')")
    full_name: str | None = Field(None, description="Full team name")
    abbreviation: str | None = Field(
        None, description="Team abbreviation (e.g., 'LAL')"
    )

    # Conference and division
    conference: str | None = Field(None, description="Conference (Eastern/Western)")
    division: str | None = Field(None, description="Division name")

    # Additional raw fields that might come from NBA API
    nickname: str | None = Field(None, description="Team nickname")
    state: str | None = Field(None, description="Team state")
    year_founded: int | None = Field(None, description="Year team was founded")


class PlayerRaw(BaseBronzeModel):
    """Raw player data model matching NBA API player endpoints."""

    # Core identifiers
    id: int = Field(..., description="NBA player ID")
    first_name: str | None = Field(None, description="Player first name")
    last_name: str | None = Field(None, description="Player last name")
    full_name: str | None = Field(None, description="Player full name")

    # Team association
    team_id: int | None = Field(None, description="Current team ID")

    # Physical attributes
    position: str | None = Field(None, description="Player position")
    jersey_number: int | None = Field(None, description="Jersey number")
    height_inches: int | None = Field(None, description="Height in inches")
    weight_pounds: int | None = Field(None, description="Weight in pounds")

    # Career info
    age: int | None = Field(None, description="Player age")
    years_experience: int | None = Field(None, description="Years of NBA experience")

    # Additional raw fields that might come from NBA API
    birthdate: str | None = Field(None, description="Birth date")
    college: str | None = Field(None, description="College attended")
    draft_year: int | None = Field(None, description="Draft year")
    draft_round: int | None = Field(None, description="Draft round")
    draft_number: int | None = Field(None, description="Draft pick number")


class ScheduleGameRaw(BaseBronzeModel):
    """Raw game/schedule data model matching NBA API game endpoints."""

    # Core identifiers
    id: int = Field(..., description="NBA game ID")
    season: str | None = Field(None, description="Season identifier")
    game_date: str | None = Field(None, description="Game date/time")

    # Team matchup
    home_team_id: int | None = Field(None, description="Home team ID")
    away_team_id: int | None = Field(None, description="Away team ID")
    visitor_team_id: int | None = Field(None, description="Visitor team ID (alt field)")

    # Game results
    home_score: int | None = Field(None, description="Home team final score")
    away_score: int | None = Field(None, description="Away team final score")
    visitor_score: int | None = Field(
        None, description="Visitor team score (alt field)"
    )

    # Game metadata
    game_type: str | None = Field(
        None, description="Game type (Regular Season, Playoffs, etc.)"
    )
    is_completed: bool | None = Field(None, description="Whether game is completed")
    status: str | None = Field(None, description="Game status")

    # Additional raw fields from NBA API
    period: int | None = Field(None, description="Current/final period")
    period_time: str | None = Field(None, description="Time remaining in period")
    arena: str | None = Field(None, description="Arena name")
    attendance: int | None = Field(None, description="Game attendance")


class PlayerStatsRaw(BaseBronzeModel):
    """Raw player statistics matching NBA API boxscore/stats endpoints."""

    # Identifiers
    player_id: int | None = Field(None, description="Player ID")
    game_id: int | None = Field(None, description="Game ID")
    team_id: int | None = Field(None, description="Team ID")

    # Game context
    minutes_played: float | str | None = Field(
        None, description="Minutes played (could be string from API)"
    )
    seconds_played: int | None = Field(
        None, description="Seconds played (some APIs use this)"
    )

    # Basic box score stats
    points: int | None = Field(None, description="Points scored")
    rebounds: int | None = Field(None, description="Total rebounds")
    assists: int | None = Field(None, description="Assists")
    steals: int | None = Field(None, description="Steals")
    blocks: int | None = Field(None, description="Blocks")
    turnovers: int | None = Field(None, description="Turnovers")
    fouls: int | None = Field(None, description="Personal fouls")

    # Detailed rebounds (some APIs split these)
    offensive_rebounds: int | None = Field(None, description="Offensive rebounds")
    defensive_rebounds: int | None = Field(None, description="Defensive rebounds")

    # Shooting stats
    field_goals_made: int | None = Field(None, description="Field goals made")
    field_goals_attempted: int | None = Field(None, description="Field goals attempted")
    three_pointers_made: int | None = Field(None, description="Three pointers made")
    three_pointers_attempted: int | None = Field(
        None, description="Three pointers attempted"
    )
    free_throws_made: int | None = Field(None, description="Free throws made")
    free_throws_attempted: int | None = Field(None, description="Free throws attempted")

    # Advanced stats that might be in raw API
    plus_minus: int | None = Field(None, description="Plus/minus rating")
    technical_fouls: int | None = Field(None, description="Technical fouls")
    flagrant_fouls: int | None = Field(None, description="Flagrant fouls")

    # Raw API fields that vary by endpoint
    start_position: str | None = Field(None, description="Starting position")
    comment: str | None = Field(None, description="Any comments about performance")


class TeamStatsRaw(BaseBronzeModel):
    """Raw team statistics matching NBA API team stats endpoints."""

    # Identifiers
    team_id: int | None = Field(None, description="Team ID")
    game_id: int | None = Field(None, description="Game ID")

    # Team totals - basic box score
    points: int | None = Field(None, description="Total points scored")
    rebounds: int | None = Field(None, description="Total rebounds")
    assists: int | None = Field(None, description="Total assists")
    steals: int | None = Field(None, description="Total steals")
    blocks: int | None = Field(None, description="Total blocks")
    turnovers: int | None = Field(None, description="Total turnovers")
    fouls: int | None = Field(None, description="Total fouls")

    # Detailed rebounds
    offensive_rebounds: int | None = Field(None, description="Total offensive rebounds")
    defensive_rebounds: int | None = Field(None, description="Total defensive rebounds")

    # Shooting stats
    field_goals_made: int | None = Field(None, description="Total field goals made")
    field_goals_attempted: int | None = Field(
        None, description="Total field goals attempted"
    )
    three_pointers_made: int | None = Field(
        None, description="Total three pointers made"
    )
    three_pointers_attempted: int | None = Field(
        None, description="Total three pointers attempted"
    )
    free_throws_made: int | None = Field(None, description="Total free throws made")
    free_throws_attempted: int | None = Field(
        None, description="Total free throws attempted"
    )

    # Game flow stats
    largest_lead: int | None = Field(None, description="Largest lead in the game")
    timeouts_remaining: int | None = Field(None, description="Timeouts remaining")
    fast_break_points: int | None = Field(None, description="Fast break points")
    points_in_paint: int | None = Field(None, description="Points in the paint")
    second_chance_points: int | None = Field(None, description="Second chance points")

    # Team performance indicators from NBA API
    technical_fouls: int | None = Field(None, description="Team technical fouls")
    flagrant_fouls: int | None = Field(None, description="Team flagrant fouls")
    team_rebounds: int | None = Field(
        None, description="Team rebounds (not attributed to players)"
    )


class PlayByPlayRaw(BaseBronzeModel):
    """Raw play-by-play data matching NBA API play-by-play endpoints."""

    # Identifiers
    game_id: int | None = Field(None, description="Game ID")
    event_id: int | None = Field(None, description="Event ID")
    event_num: int | None = Field(None, description="Event number in sequence")

    # Timing
    period: int | None = Field(None, description="Period/quarter number")
    time_remaining: str | None = Field(None, description="Time remaining in period")
    elapsed_time: str | None = Field(None, description="Elapsed time")

    # Event details
    event_type: str | None = Field(None, description="Type of play/event")
    action_type: str | None = Field(
        None, description="Specific action within event type"
    )
    description: str | None = Field(None, description="Text description of play")

    # Player/team involved
    player1_id: int | None = Field(None, description="Primary player ID")
    player1_name: str | None = Field(None, description="Primary player name")
    player1_team_id: int | None = Field(None, description="Primary player's team ID")

    player2_id: int | None = Field(
        None, description="Secondary player ID (assists, fouls, etc.)"
    )
    player2_name: str | None = Field(None, description="Secondary player name")
    player2_team_id: int | None = Field(None, description="Secondary player's team ID")

    player3_id: int | None = Field(None, description="Tertiary player ID (rare)")
    player3_name: str | None = Field(None, description="Tertiary player name")
    player3_team_id: int | None = Field(None, description="Tertiary player's team ID")

    # Score tracking
    home_score: int | None = Field(None, description="Home team score after play")
    away_score: int | None = Field(None, description="Away team score after play")

    # Location data (for shots)
    location_x: float | None = Field(None, description="X coordinate on court")
    location_y: float | None = Field(None, description="Y coordinate on court")
    shot_distance: float | None = Field(None, description="Shot distance in feet")

    # Additional context
    video_available: bool | None = Field(None, description="Whether video is available")
    score_margin: int | None = Field(None, description="Score margin after play")


class BoxScoreRaw(BaseBronzeModel):
    """Raw boxscore data container matching NBA API boxscore endpoints."""

    # Game metadata
    game_id: int | None = Field(None, description="Game ID")
    game_date: str | None = Field(None, description="Game date")

    # Team information
    home_team: TeamRaw | None = Field(None, description="Home team data")
    away_team: TeamRaw | None = Field(None, description="Away team data")

    # Team stats
    home_team_stats: TeamStatsRaw | None = Field(
        None, description="Home team statistics"
    )
    away_team_stats: TeamStatsRaw | None = Field(
        None, description="Away team statistics"
    )

    # Player stats (lists of player statistics)
    home_players: list[PlayerStatsRaw] | None = Field(
        None, description="Home team player stats"
    )
    away_players: list[PlayerStatsRaw] | None = Field(
        None, description="Away team player stats"
    )

    # Game officials and metadata
    officials: list[str] | None = Field(None, description="Game officials")
    arena: str | None = Field(None, description="Arena name")
    attendance: int | None = Field(None, description="Game attendance")

    # Additional raw fields from boxscore API
    inactive_players: list[dict[str, Any]] | None = Field(
        None, description="Inactive players list"
    )
    available_video: bool | None = Field(
        None, description="Whether game video is available"
    )


# Schema generation utilities for Bronze layer
def generate_bronze_json_schema(model_class: type[BaseBronzeModel]) -> dict[str, Any]:
    """Generate JSON schema for a Bronze layer model."""
    return model_class.model_json_schema()


def generate_all_bronze_schemas() -> dict[str, dict[str, Any]]:
    """Generate JSON schemas for all Bronze layer models."""
    models = {
        "TeamRaw": TeamRaw,
        "PlayerRaw": PlayerRaw,
        "ScheduleGameRaw": ScheduleGameRaw,
        "PlayerStatsRaw": PlayerStatsRaw,
        "TeamStatsRaw": TeamStatsRaw,
        "PlayByPlayRaw": PlayByPlayRaw,
        "BoxScoreRaw": BoxScoreRaw,
    }

    return {
        name: generate_bronze_json_schema(model_class)
        for name, model_class in models.items()
    }
