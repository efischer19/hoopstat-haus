"""
Data transformation utilities for basketball statistics.

Provides common transformations, calculations, and normalization functions.
Enhanced with configurable rules engine integration.
"""

import re
from typing import Any

from .rules_engine import DataCleaningRulesEngine


def normalize_team_name(team_name: str, use_rules_engine: bool = True) -> str:
    """
    Normalize team names to a standard format.

    Args:
        team_name: Raw team name
        use_rules_engine: Whether to use the configurable rules engine

    Returns:
        Normalized team name

    Example:
        >>> normalize_team_name("lakers")
        "Los Angeles Lakers"
        >>> normalize_team_name("LA Lakers")
        "Los Angeles Lakers"
    """
    if use_rules_engine:
        try:
            engine = DataCleaningRulesEngine()
            result = engine.standardize_team_name(team_name)
            if result.success:
                return result.transformed_value
            else:
                # If rules engine fails, fall back to original logic
                pass
        except Exception:
            # Fallback to original logic if rules engine fails
            pass

    # Original logic as fallback
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


def standardize_position(position: str, use_rules_engine: bool = True) -> str:
    """
    Standardize player position to common abbreviations.

    Args:
        position: Raw position string
        use_rules_engine: Whether to use the configurable rules engine

    Returns:
        Standardized position abbreviation

    Example:
        >>> standardize_position("Point Guard")
        "PG"
        >>> standardize_position("center")
        "C"
    """
    if use_rules_engine:
        try:
            engine = DataCleaningRulesEngine()
            result = engine.standardize_position(position)
            return result.transformed_value if result.success else position
        except Exception:
            # Fallback to original logic if rules engine fails
            pass

    # Original logic as fallback
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


def clean_and_transform_record(
    record: dict[str, Any],
    entity_type: str = "player_stats",
    use_rules_engine: bool = True,
) -> dict[str, Any]:
    """
    Apply comprehensive cleaning and transformation to a single record.

    Args:
        record: Dictionary containing raw data
        entity_type: Type of entity (player_stats, team_stats, game_stats)
        use_rules_engine: Whether to use the configurable rules engine

    Returns:
        Cleaned and transformed record

    Example:
        >>> record = {"team_name": "lakers", "points": "25", "position": "point guard"}
        >>> clean_and_transform_record(record)
        {"team_name": "Los Angeles Lakers", "points": 25, "position": "PG"}
    """
    if use_rules_engine:
        try:
            engine = DataCleaningRulesEngine()
            cleaned_records, _ = engine.process_batch([record], entity_type)
            return cleaned_records[0] if cleaned_records else record
        except Exception:
            # Fallback to basic cleaning if rules engine fails
            pass

    # Basic fallback cleaning
    cleaned = record.copy()

    # Apply basic transformations
    if "team_name" in cleaned:
        cleaned["team_name"] = normalize_team_name(cleaned["team_name"], False)

    if "position" in cleaned:
        cleaned["position"] = standardize_position(cleaned["position"], False)

    # Basic numeric cleaning
    for field in ["points", "rebounds", "assists", "steals", "blocks", "turnovers"]:
        if field in cleaned and isinstance(cleaned[field], str):
            try:
                cleaned[field] = int(cleaned[field])
            except (ValueError, TypeError):
                pass

    return cleaned


def clean_batch(
    records: list[dict[str, Any]],
    entity_type: str = "player_stats",
    batch_size: int = 1000,
) -> list[dict[str, Any]]:
    """
    Clean a batch of records efficiently.

    Args:
        records: List of records to clean
        entity_type: Type of entity (player_stats, team_stats, game_stats)
        batch_size: Number of records to process in each batch

    Returns:
        List of cleaned records

    Example:
        >>> records = [{"team_name": "lakers"}, {"team_name": "warriors"}]
        >>> clean_batch(records)
        [{"team_name": "Los Angeles Lakers"}, {"team_name": "Golden State Warriors"}]
    """
    try:
        engine = DataCleaningRulesEngine()

        # Process in batches for performance
        all_cleaned = []
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            cleaned_batch, _ = engine.process_batch(batch, entity_type)
            all_cleaned.extend(cleaned_batch)

        return all_cleaned

    except Exception:
        # Fallback to individual record cleaning
        return [
            clean_and_transform_record(record, entity_type, False) for record in records
        ]


def validate_and_standardize_season(season_str: str) -> str | None:
    """
    Validate and standardize NBA season format.

    Args:
        season_str: Raw season string

    Returns:
        Standardized season string (e.g., "2023-24") or None if invalid

    Example:
        >>> validate_and_standardize_season("2023-2024")
        "2023-24"
        >>> validate_and_standardize_season("23-24")
        "2023-24"
    """
    if not season_str or not isinstance(season_str, str):
        return None

    season_str = season_str.strip()

    # Handle full year format: "2023-2024" -> "2023-24"
    if re.match(r"^\d{4}-\d{4}$", season_str):
        start_year, end_year = season_str.split("-")
        if int(end_year) == int(start_year) + 1:
            return f"{start_year}-{end_year[-2:]}"

    # Handle short year format: "23-24" -> "2023-24"
    if re.match(r"^\d{2}-\d{2}$", season_str):
        start_year, end_year = season_str.split("-")
        # Assume 21st century for NBA seasons
        full_start = f"20{start_year}"
        full_end = f"20{end_year}"
        if int(full_end) == int(full_start) + 1:
            return f"{full_start}-{end_year}"

    # Already in correct format
    if re.match(r"^\d{4}-\d{2}$", season_str):
        return season_str

    return None
