"""
Data models for basketball statistics - Backward Compatibility Re-export Module.

This module maintains backward compatibility by re-exporting all models from
the new layered structure (Bronze/Silver/Gold). Import paths remain unchanged
to prevent breaking existing code.

For new code, prefer importing directly from:
- bronze_models for raw NBA API data
- silver_models for cleaned/standardized data
- gold_models for computed analytics data
"""

from typing import Any

# Re-export Bronze layer models for completeness
from .bronze_models import (
    BaseBronzeModel,
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

# Re-export Gold layer models (maintain existing API)
from .gold_models import (
    BaseGoldModel,
    GoldPlayerDailyStats,
    GoldPlayerSeasonSummary,
    GoldTeamDailyStats,
    generate_all_gold_schemas,
    generate_gold_json_schema,
)

# Re-export core types and utilities for backward compatibility
# Re-export Silver layer models (maintain existing API)
from .silver_models import (
    BaseSilverModel,
    DataLineage,
    GameStats,
    PlayerStats,
    SchemaEvolution,
    TeamStats,
    ValidationMode,
    generate_all_silver_schemas,
    get_schema_version,
)
from .silver_models import (
    generate_silver_json_schema as generate_json_schema,  # Maintain existing name
)


# Comprehensive schema generation utility
def generate_all_schemas() -> dict[str, dict[str, dict[str, Any]]]:
    """Generate JSON schemas for all layers (Bronze/Silver/Gold)."""
    return {
        "bronze": generate_all_bronze_schemas(),
        "silver": generate_all_silver_schemas(),
        "gold": generate_all_gold_schemas(),
    }


# For backward compatibility, maintain original function signatures
__all__ = [
    # Core types and utilities
    "ValidationMode",
    "DataLineage",
    "get_schema_version",
    "SchemaEvolution",
    # Base models
    "BaseBronzeModel",
    "BaseSilverModel",
    "BaseGoldModel",
    # Silver layer models (main API)
    "PlayerStats",
    "TeamStats",
    "GameStats",
    # Gold layer models
    "GoldPlayerDailyStats",
    "GoldPlayerSeasonSummary",
    "GoldTeamDailyStats",
    # Bronze layer models
    "TeamRaw",
    "PlayerRaw",
    "ScheduleGameRaw",
    "PlayerStatsRaw",
    "TeamStatsRaw",
    "PlayByPlayRaw",
    "BoxScoreRaw",
    # Schema generation
    "generate_json_schema",  # Backward compatible name
    "generate_bronze_json_schema",
    "generate_gold_json_schema",
    "generate_all_bronze_schemas",
    "generate_all_silver_schemas",
    "generate_all_gold_schemas",
    "generate_all_schemas",
]
