"""
Hoopstat Data Processing Utilities

A shared library for basketball statistics data processing, validation,
transformation, and quality checking.
"""

from .models import GameStats, PlayerStats, TeamStats
from .quality import check_data_completeness, detect_outliers
from .rules_engine import DataCleaningRulesEngine, TransformationResult
from .transforms import (
    calculate_efficiency_rating,
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
    # Models
    "PlayerStats",
    "TeamStats",
    "GameStats",
    # Validation
    "validate_player_stats",
    "validate_team_stats",
    "validate_game_stats",
    "validate_stat_ranges",
    # Transforms
    "normalize_team_name",
    "calculate_efficiency_rating",
    "standardize_position",
    "clean_and_transform_record",
    "clean_batch",
    "validate_and_standardize_season",
    # Quality
    "check_data_completeness",
    "detect_outliers",
    # Rules Engine
    "DataCleaningRulesEngine",
    "TransformationResult",
]
