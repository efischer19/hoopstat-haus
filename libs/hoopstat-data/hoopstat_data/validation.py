"""
Data validation functions for basketball statistics.

Provides common validation logic for ensuring data quality and consistency.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_player_stats(stats_data: dict[str, Any]) -> bool:
    """
    Validate player statistics data for consistency and logical constraints.

    Args:
        stats_data: Dictionary containing player statistics

    Returns:
        bool: True if all validations pass, False otherwise

    Example:
        >>> stats = {"points": 25, "rebounds": 10, "assists": 5}
        >>> validate_player_stats(stats)
        True
    """
    try:
        # Required fields check
        required_fields = ["points", "rebounds", "assists"]
        for field in required_fields:
            if field not in stats_data:
                logger.warning(f"Missing required field: {field}")
                return False

        # Non-negative stats check
        non_negative_fields = [
            "points",
            "rebounds",
            "assists",
            "steals",
            "blocks",
            "turnovers",
        ]
        for field in non_negative_fields:
            if field in stats_data and stats_data[field] < 0:
                logger.warning(
                    f"Invalid negative value for {field}: {stats_data[field]}"
                )
                return False

        # Shooting percentage logic
        if "field_goals_made" in stats_data and "field_goals_attempted" in stats_data:
            made = stats_data["field_goals_made"]
            attempted = stats_data["field_goals_attempted"]
            if made > attempted:
                logger.warning(
                    f"Field goals made ({made}) cannot exceed attempted ({attempted})"
                )
                return False

        # Reasonable ranges check
        if stats_data.get("points", 0) > 200:  # Unreasonably high for a single game
            logger.warning(f"Unusually high points: {stats_data['points']}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating player stats: {e}")
        return False


def validate_team_stats(stats_data: dict[str, Any]) -> bool:
    """
    Validate team statistics data for consistency and logical constraints.

    Args:
        stats_data: Dictionary containing team statistics

    Returns:
        bool: True if all validations pass, False otherwise

    Example:
        >>> stats = {"team_name": "Lakers", "points": 120, "field_goals_made": 45}
        >>> validate_team_stats(stats)
        True
    """
    try:
        # Required fields
        required_fields = ["team_name", "points"]
        for field in required_fields:
            if field not in stats_data or stats_data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False

        # Non-negative stats
        non_negative_fields = ["points", "field_goals_made", "rebounds", "assists"]
        for field in non_negative_fields:
            if field in stats_data and stats_data[field] < 0:
                logger.warning(
                    f"Invalid negative value for {field}: {stats_data[field]}"
                )
                return False

        # Team name validation
        team_name = stats_data.get("team_name", "")
        if (
            not team_name
            or not isinstance(team_name, str)
            or len(team_name.strip()) == 0
        ):
            logger.warning("Invalid team name")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating team stats: {e}")
        return False


def validate_game_stats(stats_data: dict[str, Any]) -> bool:
    """
    Validate game statistics data for consistency and logical constraints.

    Args:
        stats_data: Dictionary containing game statistics

    Returns:
        bool: True if all validations pass, False otherwise

    Example:
        >>> stats = {"home_score": 110, "away_score": 105, "game_id": "game_123"}
        >>> validate_game_stats(stats)
        True
    """
    try:
        # Required fields
        required_fields = ["game_id", "home_score", "away_score"]
        for field in required_fields:
            if field not in stats_data or stats_data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False

        # Score validation
        home_score = stats_data["home_score"]
        away_score = stats_data["away_score"]

        if not isinstance(home_score, int) or not isinstance(away_score, int):
            logger.warning("Scores must be integers")
            return False

        if home_score < 0 or away_score < 0:
            logger.warning("Scores cannot be negative")
            return False

        # Reasonable score ranges (NBA games typically 80-150 points)
        if home_score > 200 or away_score > 200:
            logger.warning(f"Unusually high scores: {home_score}, {away_score}")

        if home_score < 50 or away_score < 50:
            logger.warning(f"Unusually low scores: {home_score}, {away_score}")

        return True

    except Exception as e:
        logger.error(f"Error validating game stats: {e}")
        return False


def validate_stat_ranges(
    stats_data: dict[str, Any], stat_ranges: dict[str, tuple] | None = None
) -> list[str]:
    """
    Validate that statistics fall within expected ranges.

    Args:
        stats_data: Dictionary containing statistics to validate
        stat_ranges: Optional dictionary of (min, max) ranges for each stat

    Returns:
        List of validation error messages (empty if all valid)

    Example:
        >>> stats = {"points": 25, "rebounds": -5}
        >>> validate_stat_ranges(stats)
        ['rebounds value -5 is outside expected range (0, 50)']
    """
    if stat_ranges is None:
        # Default ranges for common basketball stats
        stat_ranges = {
            "points": (0, 100),
            "rebounds": (0, 50),
            "assists": (0, 30),
            "steals": (0, 15),
            "blocks": (0, 15),
            "turnovers": (0, 20),
            "field_goals_made": (0, 50),
            "three_pointers_made": (0, 25),
            "free_throws_made": (0, 30),
        }

    errors = []

    for stat_name, value in stats_data.items():
        if stat_name in stat_ranges and value is not None:
            min_val, max_val = stat_ranges[stat_name]
            if not (min_val <= value <= max_val):
                errors.append(
                    f"{stat_name} value {value} is outside expected range "
                    f"({min_val}, {max_val})"
                )

    return errors
