"""
Hoopstat Data Processing Utilities

A shared library for basketball statistics data processing, validation,
transformation, quality checking, and Gold layer partitioning.
"""

from .models import (
    GameStats,
    GoldPlayerDailyStats,
    GoldPlayerSeasonSummary,
    GoldTeamDailyStats,
    PlayerStats,
    TeamStats,
)
from .partitioning import (
    FileSizeOptimizer,
    PartitionHealthChecker,
    PartitionType,
    QueryPatternOptimizer,
    S3PartitionKey,
    create_player_daily_partition,
    create_player_season_partition,
    create_team_daily_partition,
)
from .quality import check_data_completeness, detect_outliers
from .transforms import (
    calculate_efficiency_rating,
    normalize_team_name,
    standardize_position,
)
from .validation import (
    validate_game_stats,
    validate_player_stats,
    validate_stat_ranges,
    validate_team_stats,
)

__version__ = "0.1.0"

__all__ = [
    # Silver Layer Models
    "PlayerStats",
    "TeamStats",
    "GameStats",
    # Gold Layer Models
    "GoldPlayerDailyStats",
    "GoldPlayerSeasonSummary",
    "GoldTeamDailyStats",
    # Validation
    "validate_player_stats",
    "validate_team_stats",
    "validate_game_stats",
    "validate_stat_ranges",
    # Transforms
    "normalize_team_name",
    "calculate_efficiency_rating",
    "standardize_position",
    # Quality
    "check_data_completeness",
    "detect_outliers",
    # Partitioning
    "S3PartitionKey",
    "PartitionType",
    "FileSizeOptimizer",
    "QueryPatternOptimizer",
    "PartitionHealthChecker",
    "create_player_daily_partition",
    "create_player_season_partition",
    "create_team_daily_partition",
]
