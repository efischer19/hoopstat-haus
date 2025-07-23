"""
Data transformation utilities for basketball statistics.

Provides common transformations, calculations, and normalization functions.
"""

import re
from typing import Any


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team names to a standard format.

    Args:
        team_name: Raw team name

    Returns:
        Normalized team name

    Example:
        >>> normalize_team_name("lakers")
        "Lakers"
        >>> normalize_team_name("LA Lakers")
        "Lakers"
    """
    if not team_name or not isinstance(team_name, str):
        return ""

    # Remove common prefixes and clean up
    name = team_name.strip()

    # Common team name mappings
    team_mappings = {
        "la lakers": "Lakers",
        "los angeles lakers": "Lakers",
        "l.a. lakers": "Lakers",
        "golden state warriors": "Warriors",
        "gs warriors": "Warriors",
        "boston celtics": "Celtics",
        "chicago bulls": "Bulls",
        "miami heat": "Heat",
        "san antonio spurs": "Spurs",
    }

    name_lower = name.lower()
    if name_lower in team_mappings:
        return team_mappings[name_lower]

    # Default: capitalize first letter of each word, remove extra spaces
    return " ".join(word.capitalize() for word in re.split(r"\s+", name) if word)


def calculate_efficiency_rating(stats: dict[str, Any]) -> float:
    """
    Calculate player efficiency rating (PER-like metric).

    Simplified calculation:
    (Points + Rebounds + Assists + Steals + Blocks - Turnovers) / Minutes

    Args:
        stats: Dictionary containing player statistics

    Returns:
        Efficiency rating as a float

    Example:
        >>> stats = {
        ...     "points": 25, "rebounds": 10, "assists": 5,
        ...     "steals": 2, "blocks": 1, "turnovers": 3, "minutes_played": 35
        ... }
        >>> calculate_efficiency_rating(stats)
        1.14
    """
    try:
        points = stats.get("points", 0)
        rebounds = stats.get("rebounds", 0)
        assists = stats.get("assists", 0)
        steals = stats.get("steals", 0)
        blocks = stats.get("blocks", 0)
        turnovers = stats.get("turnovers", 0)
        minutes = stats.get("minutes_played", 1)  # Avoid division by zero

        if minutes <= 0:
            return 0.0

        positive_stats = points + rebounds + assists + steals + blocks
        efficiency = (positive_stats - turnovers) / minutes

        return round(efficiency, 2)

    except Exception:
        return 0.0


def standardize_position(position: str) -> str:
    """
    Standardize player position to common abbreviations.

    Args:
        position: Raw position string

    Returns:
        Standardized position abbreviation

    Example:
        >>> standardize_position("Point Guard")
        "PG"
        >>> standardize_position("center")
        "C"
    """
    if not position or not isinstance(position, str):
        return "UNKNOWN"

    position_clean = position.strip().lower()

    # Position mappings
    position_map = {
        "point guard": "PG",
        "pg": "PG",
        "shooting guard": "SG",
        "sg": "SG",
        "guard": "G",
        "small forward": "SF",
        "sf": "SF",
        "power forward": "PF",
        "pf": "PF",
        "forward": "F",
        "center": "C",
        "c": "C",
    }

    # Check exact matches first
    if position_clean in position_map:
        return position_map[position_clean]

    # Check partial matches
    for key, value in position_map.items():
        if key in position_clean:
            return value

    return "UNKNOWN"


def calculate_shooting_percentage(made: int, attempted: int) -> float | None:
    """
    Calculate shooting percentage with proper handling of edge cases.

    Args:
        made: Number of shots made
        attempted: Number of shots attempted

    Returns:
        Shooting percentage as decimal (0.0 to 1.0), or None if invalid

    Example:
        >>> calculate_shooting_percentage(8, 15)
        0.533
        >>> calculate_shooting_percentage(0, 0)
        None
    """
    if attempted <= 0 or made < 0 or made > attempted:
        return None

    percentage = made / attempted
    return round(percentage, 3)


def convert_minutes_to_decimal(minutes_str: str) -> float | None:
    """
    Convert minutes from "MM:SS" format to decimal minutes.

    Args:
        minutes_str: Time string in "MM:SS" format

    Returns:
        Decimal minutes, or None if invalid format

    Example:
        >>> convert_minutes_to_decimal("35:30")
        35.5
        >>> convert_minutes_to_decimal("12:45")
        12.75
    """
    if not minutes_str or not isinstance(minutes_str, str):
        return None

    try:
        if ":" in minutes_str:
            parts = minutes_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                if seconds >= 60:  # Invalid seconds
                    return None
                return minutes + (seconds / 60.0)
        else:
            # Already in decimal format
            return float(minutes_str)

    except (ValueError, IndexError):
        return None

    return None


def normalize_stat_per_game(stat_value: float, games_played: int) -> float | None:
    """
    Normalize a cumulative stat to per-game average.

    Args:
        stat_value: Cumulative statistic value
        games_played: Number of games played

    Returns:
        Per-game average, or None if invalid

    Example:
        >>> normalize_stat_per_game(250, 10)
        25.0
    """
    if games_played <= 0:
        return None

    return round(stat_value / games_played, 1)
