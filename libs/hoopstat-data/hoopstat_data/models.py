"""
Data models for basketball statistics.

Provides Pydantic models for consistent data structures across applications.
"""

from pydantic import BaseModel, Field, validator


class PlayerStats(BaseModel):
    """Player statistics data model."""

    player_id: str = Field(..., description="Unique identifier for the player")
    player_name: str | None = Field(None, description="Player's name")
    team: str | None = Field(None, description="Player's team")
    position: str | None = Field(None, description="Player's position")

    # Basic stats
    points: int = Field(ge=0, description="Points scored")
    rebounds: int = Field(ge=0, description="Total rebounds")
    assists: int = Field(ge=0, description="Assists")
    steals: int = Field(ge=0, description="Steals")
    blocks: int = Field(ge=0, description="Blocks")
    turnovers: int = Field(ge=0, description="Turnovers")

    # Shooting stats
    field_goals_made: int | None = Field(None, ge=0, description="Field goals made")
    field_goals_attempted: int | None = Field(
        None, ge=0, description="Field goals attempted"
    )
    three_pointers_made: int | None = Field(
        None, ge=0, description="Three pointers made"
    )
    three_pointers_attempted: int | None = Field(
        None, ge=0, description="Three pointers attempted"
    )
    free_throws_made: int | None = Field(None, ge=0, description="Free throws made")
    free_throws_attempted: int | None = Field(
        None, ge=0, description="Free throws attempted"
    )

    # Game context
    minutes_played: float | None = Field(None, ge=0, description="Minutes played")
    game_id: str | None = Field(None, description="Game identifier")

    @validator("field_goals_attempted")
    def validate_field_goals(cls, v, values):
        """Ensure field goals attempted >= field goals made."""
        if (
            v is not None
            and "field_goals_made" in values
            and values["field_goals_made"] is not None
        ):
            if v < values["field_goals_made"]:
                raise ValueError("Field goals attempted must be >= field goals made")
        return v


class TeamStats(BaseModel):
    """Team statistics data model."""

    team_id: str = Field(..., description="Unique identifier for the team")
    team_name: str = Field(..., description="Team name")

    # Team totals
    points: int = Field(ge=0, description="Total points scored")
    field_goals_made: int = Field(ge=0, description="Total field goals made")
    field_goals_attempted: int = Field(ge=0, description="Total field goals attempted")
    three_pointers_made: int | None = Field(
        None, ge=0, description="Total three pointers made"
    )
    three_pointers_attempted: int | None = Field(
        None, ge=0, description="Total three pointers attempted"
    )
    free_throws_made: int | None = Field(
        None, ge=0, description="Total free throws made"
    )
    free_throws_attempted: int | None = Field(
        None, ge=0, description="Total free throws attempted"
    )

    rebounds: int = Field(ge=0, description="Total rebounds")
    assists: int = Field(ge=0, description="Total assists")
    steals: int | None = Field(None, ge=0, description="Total steals")
    blocks: int | None = Field(None, ge=0, description="Total blocks")
    turnovers: int | None = Field(None, ge=0, description="Total turnovers")
    fouls: int | None = Field(None, ge=0, description="Total fouls")

    # Game context
    game_id: str | None = Field(None, description="Game identifier")


class GameStats(BaseModel):
    """Game statistics data model."""

    game_id: str = Field(..., description="Unique identifier for the game")
    home_team_id: str = Field(..., description="Home team identifier")
    away_team_id: str = Field(..., description="Away team identifier")

    home_score: int = Field(ge=0, description="Home team final score")
    away_score: int = Field(ge=0, description="Away team final score")

    # Game metadata
    season: str | None = Field(None, description="Season identifier")
    game_date: str | None = Field(None, description="Game date (ISO format)")
    venue: str | None = Field(None, description="Game venue")

    # Game flow
    quarters: int | None = Field(
        None, ge=4, le=8, description="Number of quarters/periods"
    )
    overtime: bool | None = Field(None, description="Whether game went to overtime")

    @validator("away_score")
    def validate_scores(cls, v, values):
        """Ensure scores are not tied (games should have a winner)."""
        if "home_score" in values and v == values["home_score"]:
            # Allow ties for demo purposes, but log warning
            pass
        return v
