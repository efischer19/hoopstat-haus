"""
Hoopstat Data Processing Utilities

A shared library for basketball statistics data processing, validation,
transformation, quality checking, and Gold layer partitioning.
"""

from .models import (
    BoxScoreRaw,
    # Core types
    DataLineage,
    # Silver layer models (main API - backward compatible)
    GameStats,
    # Gold layer models
    GoldPlayerDailyStats,
    GoldPlayerSeasonSummary,
    GoldTeamDailyStats,
    PlayByPlayRaw,
    PlayerRaw,
    PlayerStats,
    PlayerStatsRaw,
    ScheduleGameRaw,
    # Bronze layer models
    TeamRaw,
    TeamStats,
    TeamStatsRaw,
    ValidationMode,
    generate_all_schemas,
    # Schema generation
    generate_json_schema,
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
from .rules_engine import DataCleaningRulesEngine, TransformationResult
from .transforms import (
    PlayerSeasonAggregator,
    TeamSeasonAggregator,
    calculate_assists_per_turnover,
    calculate_defensive_rating,
    calculate_effective_field_goal_percentage,
    calculate_efficiency_rating,
    calculate_free_throw_rate,
    calculate_offensive_rating,
    calculate_offensive_rebound_percentage,
    calculate_pace,
    calculate_points_per_shot,
    calculate_possessions,
    calculate_true_shooting_percentage,
    calculate_turnover_percentage,
    calculate_usage_rate,
    clean_and_transform_record,
    clean_batch,
    normalize_team_name,
    standardize_position,
    validate_and_standardize_season,
)
from .validation import (
    validate_game_stats,
    validate_player_stats,
    validate_stat_ranges,
    validate_team_stats,
)

__version__ = "0.1.0"

__all__ = [
    # Core types
    "DataLineage",
    "ValidationMode",
    # Silver Layer Models (main backward-compatible API)
    "PlayerStats",
    "TeamStats",
    "GameStats",
    # Gold Layer Models
    "GoldPlayerDailyStats",
    "GoldPlayerSeasonSummary",
    "GoldTeamDailyStats",
    # Bronze Layer Models
    "TeamRaw",
    "PlayerRaw",
    "ScheduleGameRaw",
    "PlayerStatsRaw",
    "TeamStatsRaw",
    "PlayByPlayRaw",
    "BoxScoreRaw",
    # Schema utilities
    "generate_json_schema",
    "generate_all_schemas",
    # Validation
    "validate_player_stats",
    "validate_team_stats",
    "validate_game_stats",
    "validate_stat_ranges",
    # Transforms
    "normalize_team_name",
    "calculate_efficiency_rating",
    "calculate_true_shooting_percentage",
    "calculate_usage_rate",
    "calculate_points_per_shot",
    "calculate_assists_per_turnover",
    "calculate_possessions",
    "calculate_offensive_rating",
    "calculate_defensive_rating",
    "calculate_pace",
    "calculate_effective_field_goal_percentage",
    "calculate_turnover_percentage",
    "calculate_offensive_rebound_percentage",
    "calculate_free_throw_rate",
    "standardize_position",
    "clean_and_transform_record",
    "clean_batch",
    "validate_and_standardize_season",
    "PlayerSeasonAggregator",
    "TeamSeasonAggregator",
    # Quality
    "check_data_completeness",
    "detect_outliers",
    # Rules Engine
    "DataCleaningRulesEngine",
    "TransformationResult",
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
