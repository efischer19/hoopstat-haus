"""Data models for NBA entities using Pydantic for validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Position(str, Enum):
    """Basketball positions."""

    POINT_GUARD = "PG"
    SHOOTING_GUARD = "SG"
    SMALL_FORWARD = "SF"
    POWER_FORWARD = "PF"
    CENTER = "C"


class Conference(str, Enum):
    """NBA conferences."""

    EASTERN = "Eastern"
    WESTERN = "Western"


class Division(str, Enum):
    """NBA divisions."""

    ATLANTIC = "Atlantic"
    CENTRAL = "Central"
    SOUTHEAST = "Southeast"
    NORTHWEST = "Northwest"
    PACIFIC = "Pacific"
    SOUTHWEST = "Southwest"


class GameType(str, Enum):
    """Types of NBA games."""

    REGULAR_SEASON = "Regular Season"
    PLAYOFFS = "Playoffs"
    PRESEASON = "Preseason"


class Team(BaseModel):
    """NBA team model."""

    id: int = Field(..., description="Unique team identifier")
    name: str = Field(..., description="Team name (e.g., 'Lakers')")
    city: str = Field(..., description="Team city (e.g., 'Los Angeles')")
    full_name: str = Field(
        ..., description="Full team name (e.g., 'Los Angeles Lakers')"
    )
    abbreviation: str = Field(
        ..., max_length=3, description="3-letter team abbreviation"
    )
    conference: Conference = Field(..., description="NBA conference")
    division: Division = Field(..., description="NBA division")


class Player(BaseModel):
    """NBA player model."""

    id: int = Field(..., description="Unique player identifier")
    first_name: str = Field(..., description="Player first name")
    last_name: str = Field(..., description="Player last name")
    full_name: str = Field(..., description="Full player name")
    team_id: int = Field(..., description="Current team ID")
    position: Position = Field(..., description="Primary position")
    jersey_number: int = Field(..., ge=0, le=99, description="Jersey number")
    height_inches: int = Field(..., ge=60, le=96, description="Height in inches")
    weight_pounds: int = Field(..., ge=150, le=350, description="Weight in pounds")
    age: int = Field(..., ge=18, le=50, description="Current age")
    years_experience: int = Field(
        ..., ge=0, le=25, description="Years of NBA experience"
    )


class Game(BaseModel):
    """NBA game model."""

    id: int = Field(..., description="Unique game identifier")
    season: str = Field(..., description="Season (e.g., '2023-24')")
    game_date: datetime = Field(..., description="Game date and time")
    home_team_id: int = Field(..., description="Home team ID")
    away_team_id: int = Field(..., description="Away team ID")
    home_score: int | None = Field(None, ge=0, description="Home team final score")
    away_score: int | None = Field(None, ge=0, description="Away team final score")
    game_type: GameType = Field(..., description="Type of game")
    is_completed: bool = Field(
        default=False, description="Whether the game is completed"
    )


class PlayerStats(BaseModel):
    """Player statistics for a game."""

    player_id: int = Field(..., description="Player ID")
    game_id: int = Field(..., description="Game ID")
    team_id: int = Field(..., description="Team ID")
    minutes_played: float = Field(..., ge=0, le=48, description="Minutes played")
    points: int = Field(..., ge=0, description="Points scored")
    rebounds: int = Field(..., ge=0, description="Total rebounds")
    assists: int = Field(..., ge=0, description="Assists")
    steals: int = Field(..., ge=0, description="Steals")
    blocks: int = Field(..., ge=0, description="Blocks")
    turnovers: int = Field(..., ge=0, description="Turnovers")
    fouls: int = Field(..., ge=0, description="Personal fouls")
    field_goals_made: int = Field(..., ge=0, description="Field goals made")
    field_goals_attempted: int = Field(..., ge=0, description="Field goals attempted")
    three_pointers_made: int = Field(..., ge=0, description="Three-pointers made")
    three_pointers_attempted: int = Field(
        ..., ge=0, description="Three-pointers attempted"
    )
    free_throws_made: int = Field(..., ge=0, description="Free throws made")
    free_throws_attempted: int = Field(..., ge=0, description="Free throws attempted")


class TeamStats(BaseModel):
    """Team statistics for a game."""

    team_id: int = Field(..., description="Team ID")
    game_id: int = Field(..., description="Game ID")
    points: int = Field(..., ge=0, description="Total points")
    rebounds: int = Field(..., ge=0, description="Total rebounds")
    assists: int = Field(..., ge=0, description="Total assists")
    steals: int = Field(..., ge=0, description="Total steals")
    blocks: int = Field(..., ge=0, description="Total blocks")
    turnovers: int = Field(..., ge=0, description="Total turnovers")
    fouls: int = Field(..., ge=0, description="Total fouls")
    field_goals_made: int = Field(..., ge=0, description="Total field goals made")
    field_goals_attempted: int = Field(
        ..., ge=0, description="Total field goals attempted"
    )
    three_pointers_made: int = Field(..., ge=0, description="Total three-pointers made")
    three_pointers_attempted: int = Field(
        ..., ge=0, description="Total three-pointers attempted"
    )
    free_throws_made: int = Field(..., ge=0, description="Total free throws made")
    free_throws_attempted: int = Field(
        ..., ge=0, description="Total free throws attempted"
    )
