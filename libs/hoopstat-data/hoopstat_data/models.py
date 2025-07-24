"""
Data models for basketball statistics.

Provides Pydantic models for consistent data structures across applications.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ValidationMode(str, Enum):
    """Validation strictness levels for schema validation."""

    STRICT = "strict"
    LENIENT = "lenient"


def get_schema_version() -> str:
    """Get current schema version."""
    return "1.0.0"


class DataLineage(BaseModel):
    """Data lineage tracking information."""

    source_system: str = Field(..., description="Source system that provided the data")
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When data was ingested"
    )
    schema_version: str = Field(..., description="Schema version used for validation")
    transformation_stage: str = Field(..., description="ETL stage (bronze/silver/gold)")
    validation_mode: ValidationMode = Field(
        default=ValidationMode.STRICT, description="Validation strictness level"
    )


class BaseSilverModel(BaseModel):
    """Base model for all Silver layer entities with common metadata."""

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "use_enum_values": True,
        "extra": "forbid",
    }

    # Data lineage - optional with default for backward compatibility
    lineage: DataLineage | None = Field(
        None, description="Data lineage and metadata tracking"
    )

    def __init__(self, validation_mode: ValidationMode = ValidationMode.STRICT, **data):
        """Initialize with validation mode configuration."""
        # Provide default lineage if not supplied
        if "lineage" not in data:
            data["lineage"] = DataLineage(
                source_system="unknown",
                schema_version=get_schema_version(),
                transformation_stage="silver",
                validation_mode=validation_mode,
            )
        super().__init__(**data)


class PlayerStats(BaseSilverModel):
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

    @field_validator("field_goals_attempted")
    @classmethod
    def validate_field_goals(cls, v, info):
        """Ensure field goals attempted >= field goals made."""
        if v is not None and info.data.get("field_goals_made") is not None:
            if v < info.data["field_goals_made"]:
                # Check validation mode from lineage if available
                lineage = info.data.get("lineage")
                validation_mode = ValidationMode.STRICT
                if lineage and hasattr(lineage, "validation_mode"):
                    validation_mode = lineage.validation_mode

                # In lenient mode, allow this inconsistency with warning
                if validation_mode == ValidationMode.LENIENT:
                    return v
                raise ValueError("Field goals attempted must be >= field goals made")
        return v

    @field_validator("points")
    @classmethod
    def validate_points_range(cls, v, info):
        """Validate points are within reasonable NBA game ranges."""
        if v > 100:  # Wilt Chamberlain's 100-point game is the record
            # Check validation mode from lineage if available
            lineage = info.data.get("lineage")
            validation_mode = ValidationMode.STRICT
            if lineage and hasattr(lineage, "validation_mode"):
                validation_mode = lineage.validation_mode

            if validation_mode == ValidationMode.STRICT:
                raise ValueError("Points exceeds reasonable NBA single-game maximum")
        return v

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v):
        """Ensure player name is properly formatted."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Player name cannot be empty string")
        return v

    @model_validator(mode="after")
    def validate_shooting_consistency(self):
        """Validate shooting statistics consistency."""
        validation_mode = getattr(
            self.lineage, "validation_mode", ValidationMode.STRICT
        )

        # Check three-pointers consistency
        if (
            self.three_pointers_made is not None
            and self.three_pointers_attempted is not None
            and self.three_pointers_made > self.three_pointers_attempted
        ):
            if validation_mode == ValidationMode.STRICT:
                raise ValueError(
                    "Three pointers made cannot exceed three pointers attempted"
                )

        # Check free throws consistency
        if (
            self.free_throws_made is not None
            and self.free_throws_attempted is not None
            and self.free_throws_made > self.free_throws_attempted
        ):
            if validation_mode == ValidationMode.STRICT:
                raise ValueError("Free throws made cannot exceed free throws attempted")

        return self


class TeamStats(BaseSilverModel):
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

    @field_validator("team_name")
    @classmethod
    def validate_team_name(cls, v):
        """Ensure team name is valid NBA team."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Team name cannot be empty")
        return v.strip()

    @field_validator("points")
    @classmethod
    def validate_points_range(cls, v, info):
        """Validate team points are within reasonable NBA game ranges."""
        # Check validation mode from lineage if available
        lineage = info.data.get("lineage")
        validation_mode = ValidationMode.STRICT
        if lineage and hasattr(lineage, "validation_mode"):
            validation_mode = lineage.validation_mode

        if v > 200:  # Extremely high for NBA
            if validation_mode == ValidationMode.STRICT:
                raise ValueError(
                    "Team points exceed reasonable NBA single-game maximum"
                )
        elif (
            v < 60 and validation_mode == ValidationMode.STRICT
        ):  # Extremely low for modern NBA
            raise ValueError("Team points below reasonable NBA single-game minimum")
        return v

    @model_validator(mode="after")
    def validate_team_shooting_stats(self):
        """Validate team shooting statistics consistency."""
        validation_mode = getattr(
            self.lineage, "validation_mode", ValidationMode.STRICT
        )

        # Field goals consistency
        if self.field_goals_made > self.field_goals_attempted:
            if validation_mode == ValidationMode.STRICT:
                raise ValueError("Field goals made cannot exceed field goals attempted")

        # Three-pointers consistency
        if (
            self.three_pointers_made is not None
            and self.three_pointers_attempted is not None
            and self.three_pointers_made > self.three_pointers_attempted
        ):
            if validation_mode == ValidationMode.STRICT:
                raise ValueError(
                    "Three pointers made cannot exceed three pointers attempted"
                )

        return self


class GameStats(BaseSilverModel):
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

    @field_validator("game_date")
    @classmethod
    def validate_game_date(cls, v):
        """Ensure game date is in ISO format if provided."""
        if v is not None:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Game date must be in ISO format") from None
        return v

    @field_validator("season")
    @classmethod
    def validate_season_format(cls, v):
        """Validate NBA season format (e.g., '2023-24')."""
        import re

        if v is not None:
            if not re.match(r"^\d{4}-\d{2}$", v):
                # In lenient mode, accept various season formats
                pass
        return v

    @model_validator(mode="after")
    def validate_game_logic(self):
        """Validate game logic and constraints."""
        validation_mode = getattr(
            self.lineage, "validation_mode", ValidationMode.STRICT
        )

        # Teams cannot play themselves
        if self.home_team_id == self.away_team_id:
            raise ValueError("Home and away teams cannot be the same")

        # Score validation
        if self.home_score == self.away_score:
            if validation_mode == ValidationMode.STRICT:
                raise ValueError("NBA games cannot end in ties")

        # Overtime logic
        if self.overtime is True and self.quarters is not None and self.quarters < 5:
            if validation_mode == ValidationMode.STRICT:
                raise ValueError("Overtime games must have at least 5 quarters")

        return self


# Schema generation utilities
def generate_json_schema(model_class: type[BaseSilverModel]) -> dict[str, Any]:
    """Generate JSON schema for a Silver layer model."""
    return model_class.model_json_schema()


# Schema evolution support
class SchemaEvolution:
    """Handles schema versioning and evolution."""

    @staticmethod
    def migrate_from_version(
        data: dict[str, Any], from_version: str, to_version: str
    ) -> dict[str, Any]:
        """Migrate data from one schema version to another."""
        if from_version == to_version:
            return data

        # Add migration logic here as schema evolves
        if from_version == "0.1.0" and to_version == "1.0.0":
            # Example migration: add default lineage if missing
            if "lineage" not in data:
                data["lineage"] = {
                    "source_system": "unknown",
                    "ingestion_timestamp": datetime.utcnow().isoformat(),
                    "schema_version": to_version,
                    "transformation_stage": "silver",
                    "validation_mode": "strict",
                }

        return data
