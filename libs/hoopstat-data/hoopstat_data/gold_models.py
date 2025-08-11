"""
Gold layer data models for optimized data storage and querying.

These models provide computed metrics and optimized structures for
analytics and reporting workloads with pre-computed derived fields.
"""

from typing import Any

from pydantic import Field, field_validator

from .silver_models import (
    BaseSilverModel,
    DataLineage,
    ValidationMode,
    get_schema_version,
)


class BaseGoldModel(BaseSilverModel):
    """Base model for all Gold layer entities with computed metrics."""

    def __init__(self, validation_mode: ValidationMode = ValidationMode.STRICT, **data):
        """Initialize with Gold transformation stage."""
        # Provide default lineage if not supplied
        if "lineage" not in data:
            data["lineage"] = DataLineage(
                source_system="silver-to-gold-etl",
                schema_version=get_schema_version(),
                transformation_stage="gold",
                validation_mode=validation_mode,
            )
        elif data["lineage"]:
            # Update transformation stage for existing lineage
            data["lineage"].transformation_stage = "gold"
        super().__init__(validation_mode, **data)


class GoldPlayerDailyStats(BaseGoldModel):
    """Gold layer player daily statistics with pre-computed metrics."""

    # Inherit all Silver layer fields from PlayerStats base
    player_id: str = Field(..., description="Unique identifier for the player")
    player_name: str | None = Field(None, description="Player's name")
    team: str | None = Field(None, description="Player's team")
    position: str | None = Field(None, description="Player's position")

    # Basic stats (same as Silver)
    points: int = Field(ge=0, description="Points scored")
    rebounds: int = Field(ge=0, description="Total rebounds")
    assists: int = Field(ge=0, description="Assists")
    steals: int = Field(ge=0, description="Steals")
    blocks: int = Field(ge=0, description="Blocks")
    turnovers: int = Field(ge=0, description="Turnovers")

    # Shooting stats (same as Silver)
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

    # Game context (same as Silver)
    minutes_played: float | None = Field(None, ge=0, description="Minutes played")
    game_id: str | None = Field(None, description="Game identifier")
    game_date: str | None = Field(None, description="Game date (YYYY-MM-DD)")

    # Gold layer computed metrics
    efficiency_rating: float | None = Field(
        None, description="Player efficiency rating (PER-like metric)"
    )
    true_shooting_percentage: float | None = Field(
        None, ge=0, le=1, description="True shooting percentage"
    )
    usage_rate: float | None = Field(
        None, ge=0, le=1, description="Usage rate percentage"
    )
    plus_minus: int | None = Field(None, description="Plus/minus rating")

    # Partition metadata
    partition_key: str | None = Field(None, description="S3 partition key")
    season: str | None = Field(None, description="NBA season (e.g., '2023-24')")

    @field_validator("true_shooting_percentage")
    @classmethod
    def validate_ts_percentage(cls, v):
        """Validate true shooting percentage is reasonable."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("True shooting percentage must be between 0 and 1")
        return v

    @field_validator("season")
    @classmethod
    def validate_season_format(cls, v):
        """Validate NBA season format."""
        import re

        if v is not None:
            if not re.match(r"^\d{4}-\d{2}$", v):
                raise ValueError("Season must be in format 'YYYY-YY' (e.g., '2023-24')")
        return v


class GoldPlayerSeasonSummary(BaseGoldModel):
    """Gold layer player season summary with aggregated statistics."""

    player_id: str = Field(..., description="Unique identifier for the player")
    player_name: str | None = Field(None, description="Player's name")
    season: str = Field(..., description="NBA season (e.g., '2023-24')")
    team: str | None = Field(None, description="Primary team for the season")

    # Season totals
    total_games: int = Field(ge=0, description="Total games played")
    total_minutes: float = Field(ge=0, description="Total minutes played")

    # Per-game averages
    points_per_game: float = Field(ge=0, description="Points per game")
    rebounds_per_game: float = Field(ge=0, description="Rebounds per game")
    assists_per_game: float = Field(ge=0, description="Assists per game")
    steals_per_game: float = Field(ge=0, description="Steals per game")
    blocks_per_game: float = Field(ge=0, description="Blocks per game")
    turnovers_per_game: float = Field(ge=0, description="Turnovers per game")

    # Season shooting percentages
    field_goal_percentage: float | None = Field(
        None, ge=0, le=1, description="Season field goal percentage"
    )
    three_point_percentage: float | None = Field(
        None, ge=0, le=1, description="Season three-point percentage"
    )
    free_throw_percentage: float | None = Field(
        None, ge=0, le=1, description="Season free throw percentage"
    )

    # Advanced metrics
    efficiency_rating: float | None = Field(
        None, description="Season efficiency rating"
    )
    true_shooting_percentage: float | None = Field(
        None, ge=0, le=1, description="Season true shooting percentage"
    )
    usage_rate: float | None = Field(None, ge=0, le=1, description="Season usage rate")

    # Performance trends (month-over-month changes)
    scoring_trend: float | None = Field(
        None, description="Points per game trend (% change)"
    )
    efficiency_trend: float | None = Field(
        None, description="Efficiency rating trend (% change)"
    )

    # Partition metadata
    partition_key: str | None = Field(None, description="S3 partition key")

    @field_validator("season")
    @classmethod
    def validate_season_format(cls, v):
        """Validate NBA season format."""
        import re

        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("Season must be in format 'YYYY-YY' (e.g., '2023-24')")
        return v


class GoldTeamDailyStats(BaseGoldModel):
    """Gold layer team daily statistics with computed metrics."""

    team_id: str = Field(..., description="Unique identifier for the team")
    team_name: str = Field(..., min_length=1, description="Team name")
    game_id: str | None = Field(None, description="Game identifier")
    game_date: str | None = Field(None, description="Game date (YYYY-MM-DD)")
    season: str | None = Field(None, description="NBA season (e.g., '2023-24')")

    # Team totals (same as Silver)
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

    # Gold layer computed metrics
    offensive_rating: float | None = Field(
        None, description="Offensive rating (points per 100 possessions)"
    )
    defensive_rating: float | None = Field(
        None, description="Defensive rating (opponent points per 100 possessions)"
    )
    pace: float | None = Field(None, description="Pace (possessions per 48 minutes)")
    true_shooting_percentage: float | None = Field(
        None, ge=0, le=1, description="Team true shooting percentage"
    )

    # Game context
    opponent_team_id: str | None = Field(None, description="Opponent team identifier")
    home_game: bool | None = Field(None, description="Whether this was a home game")
    win: bool | None = Field(None, description="Whether the team won")

    # Partition metadata
    partition_key: str | None = Field(None, description="S3 partition key")


# Schema generation utilities for Gold layer
def generate_gold_json_schema(model_class: type[BaseGoldModel]) -> dict[str, Any]:
    """Generate JSON schema for a Gold layer model."""
    return model_class.model_json_schema()


def generate_all_gold_schemas() -> dict[str, dict[str, Any]]:
    """Generate JSON schemas for all Gold layer models."""
    models = {
        "GoldPlayerDailyStats": GoldPlayerDailyStats,
        "GoldPlayerSeasonSummary": GoldPlayerSeasonSummary,
        "GoldTeamDailyStats": GoldTeamDailyStats,
    }

    return {
        name: generate_gold_json_schema(model_class)
        for name, model_class in models.items()
    }
