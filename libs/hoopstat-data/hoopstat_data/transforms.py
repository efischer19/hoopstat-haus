"""
Data transformation utilities for basketball statistics.

Provides common transformations, calculations, and normalization functions.
Enhanced with configurable rules engine integration.
"""

import re
from typing import TYPE_CHECKING, Any

from .rules_engine import DataCleaningRulesEngine

if TYPE_CHECKING:
    import pandas as pd


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


def calculate_true_shooting_percentage(
    points: float, fga: int, fta: int
) -> float | None:
    """
    Calculate True Shooting Percentage.

    Formula: Points / (2 * (FGA + 0.44 * FTA))

    Args:
        points: Points scored
        fga: Field goal attempts
        fta: Free throw attempts

    Returns:
        True shooting percentage as decimal (0.0 to 1.0), or None if invalid

    Example:
        >>> calculate_true_shooting_percentage(25, 15, 4)
        0.735
    """
    if fga < 0 or fta < 0 or points < 0:
        return None

    denominator = 2 * (fga + 0.44 * fta)
    if denominator <= 0:
        return None

    ts_pct = points / denominator
    return round(ts_pct, 3)


def calculate_usage_rate(
    player_fga: int,
    player_fta: int,
    player_tov: int,
    player_minutes: float,
    team_fga: int,
    team_fta: int,
    team_tov: int,
    team_minutes: float,
) -> float | None:
    """
    Calculate Usage Rate.

    Formula: 100 * ((FGA + 0.44 * FTA + TOV) * (Team Minutes)) /
             (Minutes * (Team FGA + 0.44 * Team FTA + Team TOV))

    Args:
        player_fga: Player field goal attempts
        player_fta: Player free throw attempts
        player_tov: Player turnovers
        player_minutes: Player minutes played
        team_fga: Team field goal attempts
        team_fta: Team free throw attempts
        team_tov: Team turnovers
        team_minutes: Team total minutes (typically 240 for 48 minute game)

    Returns:
        Usage rate as percentage (0.0 to 100.0), or None if invalid

    Example:
        >>> calculate_usage_rate(15, 4, 3, 35, 85, 25, 15, 240)
        25.9
    """
    if (
        player_minutes <= 0
        or team_minutes <= 0
        or any(
            x < 0
            for x in [player_fga, player_fta, player_tov, team_fga, team_fta, team_tov]
        )
    ):
        return None

    player_possessions = player_fga + 0.44 * player_fta + player_tov
    team_possessions = team_fga + 0.44 * team_fta + team_tov

    if team_possessions <= 0:
        return None

    usage_rate = (
        100 * (player_possessions * team_minutes) / (player_minutes * team_possessions)
    )
    return round(usage_rate, 1)


def calculate_points_per_shot(points: int, fga: int, fta: int) -> float | None:
    """
    Calculate points per shot attempt (efficiency metric).

    Args:
        points: Points scored
        fga: Field goal attempts
        fta: Free throw attempts

    Returns:
        Points per shot, or None if invalid

    Example:
        >>> calculate_points_per_shot(25, 15, 4)
        1.32
    """
    total_shots = fga + fta
    if total_shots <= 0 or points < 0:
        return None

    return round(points / total_shots, 2)


def calculate_assists_per_turnover(assists: int, turnovers: int) -> float | None:
    """
    Calculate assist to turnover ratio.

    Args:
        assists: Number of assists
        turnovers: Number of turnovers

    Returns:
        Assist to turnover ratio, or None if invalid

    Example:
        >>> calculate_assists_per_turnover(7, 3)
        2.33
    """
    if turnovers <= 0 or assists < 0:
        return None if turnovers == 0 else 0.0

    return round(assists / turnovers, 2)


def calculate_possessions(
    fga: int, fta: int, offensive_rebounds: int, turnovers: int
) -> float | None:
    """
    Calculate possessions using the standard NBA formula.

    Formula: FGA - ORB + TOV + 0.44 * FTA

    Args:
        fga: Field goal attempts
        fta: Free throw attempts
        offensive_rebounds: Offensive rebounds
        turnovers: Turnovers

    Returns:
        Number of possessions, or None if invalid

    Example:
        >>> calculate_possessions(85, 25, 12, 15)
        111.0
    """
    if any(x < 0 for x in [fga, fta, offensive_rebounds, turnovers]):
        return None

    possessions = fga - offensive_rebounds + turnovers + 0.44 * fta
    return round(possessions, 1)


def calculate_offensive_rating(points: int, possessions: float) -> float | None:
    """
    Calculate Offensive Rating (points per 100 possessions).

    Args:
        points: Points scored
        possessions: Number of possessions

    Returns:
        Offensive rating, or None if invalid

    Example:
        >>> calculate_offensive_rating(110, 95.5)
        115.2
    """
    if possessions <= 0 or points < 0:
        return None

    rating = (points / possessions) * 100
    return round(rating, 1)


def calculate_defensive_rating(points_allowed: int, possessions: float) -> float | None:
    """
    Calculate Defensive Rating (points allowed per 100 possessions).

    Args:
        points_allowed: Points allowed to opponent
        possessions: Number of opponent possessions

    Returns:
        Defensive rating, or None if invalid

    Example:
        >>> calculate_defensive_rating(105, 98.2)
        107.0
    """
    if possessions <= 0 or points_allowed < 0:
        return None

    rating = (points_allowed / possessions) * 100
    return round(rating, 1)


def calculate_pace(possessions: float, minutes_played: float = 48.0) -> float | None:
    """
    Calculate Pace (possessions per 48 minutes).

    Args:
        possessions: Number of possessions
        minutes_played: Game minutes (default 48 for regulation)

    Returns:
        Pace, or None if invalid

    Example:
        >>> calculate_pace(95.5, 48.0)
        95.5
    """
    if possessions <= 0 or minutes_played <= 0:
        return None

    pace = (possessions / minutes_played) * 48
    return round(pace, 1)


def calculate_effective_field_goal_percentage(
    fgm: int, fga: int, tpm: int
) -> float | None:
    """
    Calculate Effective Field Goal Percentage.

    Formula: (FGM + 0.5 * 3PM) / FGA

    Args:
        fgm: Field goals made
        fga: Field goal attempts
        tpm: Three pointers made

    Returns:
        Effective FG%, or None if invalid

    Example:
        >>> calculate_effective_field_goal_percentage(42, 85, 12)
        0.565
    """
    if fga <= 0 or fgm < 0 or tpm < 0 or fgm > fga:
        return None

    efg_pct = (fgm + 0.5 * tpm) / fga
    return round(efg_pct, 3)


def calculate_turnover_percentage(turnovers: int, possessions: float) -> float | None:
    """
    Calculate Turnover Percentage.

    Formula: (TOV / Possessions) * 100

    Args:
        turnovers: Number of turnovers
        possessions: Number of possessions

    Returns:
        Turnover percentage, or None if invalid

    Example:
        >>> calculate_turnover_percentage(15, 95.5)
        15.7
    """
    if possessions <= 0 or turnovers < 0:
        return None

    tov_pct = (turnovers / possessions) * 100
    return round(tov_pct, 1)


def calculate_offensive_rebound_percentage(
    offensive_rebounds: int, team_fga: int, team_fgm: int
) -> float | None:
    """
    Calculate Offensive Rebound Percentage.

    Formula: ORB / (FGA - FGM) * 100

    Args:
        offensive_rebounds: Offensive rebounds
        team_fga: Team field goal attempts
        team_fgm: Team field goals made

    Returns:
        Offensive rebound percentage, or None if invalid

    Example:
        >>> calculate_offensive_rebound_percentage(12, 85, 42)
        27.9
    """
    missed_shots = team_fga - team_fgm
    if missed_shots <= 0 or offensive_rebounds < 0:
        return None

    orb_pct = (offensive_rebounds / missed_shots) * 100
    return round(orb_pct, 1)


def calculate_free_throw_rate(fta: int, fga: int) -> float | None:
    """
    Calculate Free Throw Rate.

    Formula: FTA / FGA

    Args:
        fta: Free throw attempts
        fga: Field goal attempts

    Returns:
        Free throw rate, or None if invalid

    Example:
        >>> calculate_free_throw_rate(25, 85)
        0.294
    """
    if fga <= 0 or fta < 0:
        return None

    ft_rate = fta / fga
    return round(ft_rate, 3)


class PlayerSeasonAggregator:
    """
    Aggregates Silver layer player statistics into Gold layer season summaries.

    Handles both regular season and playoff aggregations with advanced metrics
    calculations and data quality validation.
    """

    def __init__(self, validation_mode: str = "strict"):
        """
        Initialize the aggregator.

        Args:
            validation_mode: Validation strictness ("strict" or "lenient")
        """
        self.validation_mode = validation_mode

    def aggregate_season_stats(
        self, player_games: list[dict], season: str, season_type: str = "regular"
    ) -> dict:
        """
        Aggregate a player's season statistics from individual game records.

        Args:
            player_games: List of player game statistics (Silver layer format)
            season: Season identifier (e.g., "2023-24")
            season_type: "regular" or "playoff"

        Returns:
            Dictionary with aggregated season statistics and advanced metrics

        Example:
            >>> games = [
            ...     {
            ...         "points": 25, "rebounds": 8, "assists": 5,
            ...         "minutes_played": 35, ...
            ...     },
            ...     ...
            ... ]
            >>> aggregator = PlayerSeasonAggregator()
            >>> season_stats = aggregator.aggregate_season_stats(games, "2023-24")
        """
        if not player_games:
            return self._empty_season_stats(season, season_type)

        # Convert to pandas for efficient aggregation
        import pandas as pd

        df = pd.DataFrame(player_games)

        # Validate minimum data requirements
        if not self._validate_minimum_data(df):
            return self._empty_season_stats(season, season_type)

        # Calculate basic aggregations
        totals = self._calculate_totals(df)
        averages = self._calculate_averages(df, totals["total_games"])

        # Calculate advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(totals, df)

        # Calculate shooting percentages
        shooting_pcts = self._calculate_shooting_percentages(totals)

        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(totals)

        # Combine all statistics
        season_stats = {
            # Metadata
            "player_id": df.iloc[0].get("player_id"),
            "player_name": df.iloc[0].get("player_name"),
            "season": season,
            "season_type": season_type,
            "team": df.iloc[0].get("team"),  # Primary team
            # Basic totals and averages
            **totals,
            **averages,
            # Shooting percentages
            **shooting_pcts,
            # Advanced metrics
            **advanced_metrics,
            # Efficiency metrics
            **efficiency_metrics,
            # Data quality
            "data_quality_score": self._calculate_data_quality_score(df),
            "games_with_missing_data": self._count_games_with_missing_data(df),
        }

        return season_stats

    def _validate_minimum_data(self, df: "pd.DataFrame") -> bool:
        """Validate minimum data requirements for aggregation."""
        required_fields = ["points", "rebounds", "assists", "minutes_played"]

        # Check if required fields exist
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields and self.validation_mode == "strict":
            return False

        # Check for minimum games (at least 1 game with meaningful minutes)
        meaningful_games = df[df.get("minutes_played", 0) >= 10].shape[0]
        if meaningful_games == 0 and self.validation_mode == "strict":
            return False

        return True

    def _calculate_totals(self, df: "pd.DataFrame") -> dict:
        """Calculate season totals."""
        numeric_stats = [
            "points",
            "rebounds",
            "assists",
            "steals",
            "blocks",
            "turnovers",
            "field_goals_made",
            "field_goals_attempted",
            "three_pointers_made",
            "three_pointers_attempted",
            "free_throws_made",
            "free_throws_attempted",
            "minutes_played",
        ]

        totals = {
            "total_games": len(df),
            "total_minutes": df.get("minutes_played", 0).sum(),
        }

        # Calculate sums for available numeric stats
        for stat in numeric_stats:
            if stat in df.columns:
                totals[f"total_{stat}"] = df[stat].fillna(0).sum()

        return totals

    def _calculate_averages(self, df: "pd.DataFrame", total_games: int) -> dict:
        """Calculate per-game averages."""
        if total_games == 0:
            return {}

        averages = {}
        basic_stats = ["points", "rebounds", "assists", "steals", "blocks", "turnovers"]

        for stat in basic_stats:
            if stat in df.columns:
                avg_value = df[stat].fillna(0).mean()
                averages[f"{stat}_per_game"] = round(avg_value, 1)

        # Minutes per game
        if "minutes_played" in df.columns:
            averages["minutes_per_game"] = round(
                df["minutes_played"].fillna(0).mean(), 1
            )

        return averages

    def _calculate_shooting_percentages(self, totals: dict) -> dict:
        """Calculate shooting percentages."""
        percentages = {}

        # Field goal percentage
        fgm = totals.get("total_field_goals_made", 0)
        fga = totals.get("total_field_goals_attempted", 0)
        if fga > 0:
            percentages["field_goal_percentage"] = round(fgm / fga, 3)

        # Three-point percentage
        tpm = totals.get("total_three_pointers_made", 0)
        tpa = totals.get("total_three_pointers_attempted", 0)
        if tpa > 0:
            percentages["three_point_percentage"] = round(tpm / tpa, 3)

        # Free throw percentage
        ftm = totals.get("total_free_throws_made", 0)
        fta = totals.get("total_free_throws_attempted", 0)
        if fta > 0:
            percentages["free_throw_percentage"] = round(ftm / fta, 3)

        return percentages

    def _calculate_advanced_metrics(self, totals: dict, df: "pd.DataFrame") -> dict:
        """Calculate advanced basketball metrics."""
        metrics = {}

        # True Shooting Percentage
        points = totals.get("total_points", 0)
        fga = totals.get("total_field_goals_attempted", 0)
        fta = totals.get("total_free_throws_attempted", 0)

        ts_pct = calculate_true_shooting_percentage(points, fga, fta)
        if ts_pct is not None:
            metrics["true_shooting_percentage"] = ts_pct

        # Season Efficiency Rating (average of game ratings)
        if "minutes_played" in df.columns:
            game_efficiency_ratings = []
            for _, game in df.iterrows():
                game_dict = game.to_dict()
                rating = calculate_efficiency_rating(game_dict)
                if rating > 0:  # Only include meaningful games
                    game_efficiency_ratings.append(rating)

            if game_efficiency_ratings:
                metrics["efficiency_rating"] = round(
                    sum(game_efficiency_ratings) / len(game_efficiency_ratings), 2
                )

        # Usage Rate (simplified - team totals approximated)
        # Note: This is an approximation since we don't have exact team stats
        # while player was on court
        player_minutes = totals.get("total_minutes_played", 0)
        if player_minutes > 0:
            # Estimate team possessions based on league averages
            games_played = totals.get("total_games", 1)
            estimated_team_fga_per_game = 85  # League average
            estimated_team_fta_per_game = 25  # League average
            estimated_team_tov_per_game = 15  # League average

            team_fga = estimated_team_fga_per_game * games_played
            team_fta = estimated_team_fta_per_game * games_played
            team_tov = estimated_team_tov_per_game * games_played
            team_minutes = 240 * games_played  # 48 minutes * 5 players per game

            usage_rate = calculate_usage_rate(
                totals.get("total_field_goals_attempted", 0),
                totals.get("total_free_throws_attempted", 0),
                totals.get("total_turnovers", 0),
                player_minutes,
                team_fga,
                team_fta,
                team_tov,
                team_minutes,
            )
            if usage_rate is not None:
                metrics["usage_rate"] = usage_rate

        return metrics

    def _calculate_efficiency_metrics(self, totals: dict) -> dict:
        """Calculate efficiency-focused metrics."""
        metrics = {}

        # Points per shot
        points = totals.get("total_points", 0)
        fga = totals.get("total_field_goals_attempted", 0)
        fta = totals.get("total_free_throws_attempted", 0)

        pps = calculate_points_per_shot(points, fga, fta)
        if pps is not None:
            metrics["points_per_shot"] = pps

        # Assists per turnover
        assists = totals.get("total_assists", 0)
        turnovers = totals.get("total_turnovers", 0)

        apt = calculate_assists_per_turnover(assists, turnovers)
        if apt is not None:
            metrics["assists_per_turnover"] = apt

        return metrics

    def _calculate_data_quality_score(self, df: "pd.DataFrame") -> float:
        """Calculate overall data quality score for the season."""
        from .quality import calculate_data_quality_score

        # Calculate average data quality across all games
        quality_scores = []
        for _, game in df.iterrows():
            game_dict = game.to_dict()
            score = calculate_data_quality_score(game_dict)
            quality_scores.append(score)

        return (
            round(sum(quality_scores) / len(quality_scores), 3)
            if quality_scores
            else 0.0
        )

    def _count_games_with_missing_data(self, df: "pd.DataFrame") -> int:
        """Count games with significant missing data."""
        critical_fields = ["points", "rebounds", "assists", "minutes_played"]
        missing_count = 0

        for _, game in df.iterrows():
            missing_critical = sum(
                1
                for field in critical_fields
                if game.get(field) is None
                or (
                    hasattr(game.get(field), "__iter__")
                    and len(str(game.get(field)).strip()) == 0
                )
            )
            if missing_critical >= 2:  # More than half of critical fields missing
                missing_count += 1

        return missing_count

    def _empty_season_stats(self, season: str, season_type: str) -> dict:
        """Return empty season stats structure for invalid data."""
        return {
            "season": season,
            "season_type": season_type,
            "total_games": 0,
            "data_quality_score": 0.0,
            "error": "Insufficient or invalid data for aggregation",
        }


class TeamSeasonAggregator:
    """
    Aggregates Silver layer team statistics into Gold layer season summaries.

    Handles team-level analytics including efficiency ratings, Four Factors,
    pace calculations, and home/away splits with comprehensive metrics.
    """

    def __init__(self, validation_mode: str = "strict"):
        """
        Initialize the team aggregator.

        Args:
            validation_mode: Validation strictness ("strict" or "lenient")
        """
        self.validation_mode = validation_mode

    def aggregate_season_stats(
        self, team_games: list[dict], season: str, season_type: str = "regular"
    ) -> dict:
        """
        Aggregate a team's season statistics from individual game records.

        Args:
            team_games: List of team game statistics (Silver layer format)
            season: Season identifier (e.g., "2023-24")
            season_type: "regular" or "playoff"

        Returns:
            Dictionary with aggregated season statistics and advanced metrics

        Example:
            >>> games = [
            ...     {
            ...         "team_id": "1610612747", "points": 110, "points_allowed": 105,
            ...         "field_goals_made": 42, "field_goals_attempted": 85,
            ...         "offensive_rebounds": 12, "turnovers": 15, ...
            ...     },
            ...     ...
            ... ]
            >>> aggregator = TeamSeasonAggregator()
            >>> season_stats = aggregator.aggregate_season_stats(games, "2023-24")
        """
        if not team_games:
            return self._empty_season_stats(season, season_type)

        # Convert to pandas for efficient aggregation
        import pandas as pd

        df = pd.DataFrame(team_games)

        # Validate minimum data requirements
        if not self._validate_minimum_data(df):
            return self._empty_season_stats(season, season_type)

        # Calculate basic aggregations
        totals = self._calculate_totals(df)
        averages = self._calculate_averages(df, totals["total_games"])

        # Calculate advanced metrics
        efficiency_metrics = self._calculate_efficiency_metrics(totals, df)
        four_factors = self._calculate_four_factors(totals)
        shooting_metrics = self._calculate_shooting_metrics(totals)

        # Calculate splits
        home_away_splits = self._calculate_home_away_splits(df)
        monthly_splits = self._calculate_monthly_splits(df)

        # Combine all statistics
        season_stats = {
            # Metadata
            "team_id": df.iloc[0].get("team_id"),
            "team_name": df.iloc[0].get("team_name"),
            "season": season,
            "season_type": season_type,
            # Basic totals and averages
            **totals,
            **averages,
            # Advanced metrics
            **efficiency_metrics,
            **four_factors,
            **shooting_metrics,
            # Splits
            "home_away_splits": home_away_splits,
            "monthly_splits": monthly_splits,
            # Data quality
            "data_quality_score": self._calculate_data_quality_score(df),
            "games_with_missing_data": self._count_games_with_missing_data(df),
        }

        return season_stats

    def _validate_minimum_data(self, df: "pd.DataFrame") -> bool:
        """Validate minimum data requirements for aggregation."""
        required_fields = ["points", "points_allowed", "field_goals_attempted"]

        # Check if required fields exist
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields and self.validation_mode == "strict":
            return False

        # Check for minimum games
        if len(df) == 0:
            return False

        return True

    def _calculate_totals(self, df: "pd.DataFrame") -> dict:
        """Calculate season totals."""
        numeric_stats = [
            "points",
            "points_allowed",
            "field_goals_made",
            "field_goals_attempted",
            "three_pointers_made",
            "three_pointers_attempted",
            "free_throws_made",
            "free_throws_attempted",
            "offensive_rebounds",
            "defensive_rebounds",
            "total_rebounds",
            "assists",
            "steals",
            "blocks",
            "turnovers",
        ]

        totals = {"total_games": len(df)}

        # Calculate sums for available numeric stats
        for stat in numeric_stats:
            if stat in df.columns:
                totals[f"total_{stat}"] = df[stat].fillna(0).sum()

        return totals

    def _calculate_averages(self, df: "pd.DataFrame", total_games: int) -> dict:
        """Calculate per-game averages."""
        if total_games == 0:
            return {}

        averages = {}
        basic_stats = [
            "points",
            "points_allowed",
            "field_goals_made",
            "field_goals_attempted",
            "assists",
            "total_rebounds",
            "turnovers",
        ]

        for stat in basic_stats:
            if stat in df.columns:
                avg_value = df[stat].fillna(0).mean()
                averages[f"{stat}_per_game"] = round(avg_value, 1)

        return averages

    def _calculate_efficiency_metrics(self, totals: dict, df: "pd.DataFrame") -> dict:
        """Calculate team efficiency metrics."""
        metrics = {}

        # Calculate possessions for each game and get average
        game_possessions = []
        for _, game in df.iterrows():
            possessions = calculate_possessions(
                game.get("field_goals_attempted", 0),
                game.get("free_throws_attempted", 0),
                game.get("offensive_rebounds", 0),
                game.get("turnovers", 0),
            )
            if possessions:
                game_possessions.append(possessions)

        if game_possessions:
            avg_possessions = sum(game_possessions) / len(game_possessions)
            metrics["average_possessions_per_game"] = round(avg_possessions, 1)

            # Offensive Rating
            total_points = totals.get("total_points", 0)
            total_possessions = sum(game_possessions)
            if total_possessions > 0:
                off_rating = calculate_offensive_rating(total_points, total_possessions)
                if off_rating:
                    metrics["offensive_rating"] = off_rating

            # Defensive Rating (using points allowed and opponent possessions)
            total_points_allowed = totals.get("total_points_allowed", 0)
            # Estimate opponent possessions (simplified)
            opp_possessions = total_possessions  # Approximately equal in regulation
            def_rating = calculate_defensive_rating(
                total_points_allowed, opp_possessions
            )
            if def_rating:
                metrics["defensive_rating"] = def_rating

            # Net Rating
            if "offensive_rating" in metrics and "defensive_rating" in metrics:
                metrics["net_rating"] = round(
                    metrics["offensive_rating"] - metrics["defensive_rating"], 1
                )

            # Pace
            pace = calculate_pace(avg_possessions)
            if pace:
                metrics["pace"] = pace

        return metrics

    def _calculate_four_factors(self, totals: dict) -> dict:
        """Calculate the Four Factors."""
        factors = {}

        # Effective Field Goal Percentage
        fgm = totals.get("total_field_goals_made", 0)
        fga = totals.get("total_field_goals_attempted", 0)
        tpm = totals.get("total_three_pointers_made", 0)

        efg_pct = calculate_effective_field_goal_percentage(fgm, fga, tpm)
        if efg_pct:
            factors["effective_field_goal_percentage"] = efg_pct

        # Turnover Percentage (estimated based on average possessions)
        turnovers = totals.get("total_turnovers", 0)
        games = totals.get("total_games", 1)
        # Rough estimate of possessions per game
        est_possessions_per_game = 95  # League average
        total_possessions = est_possessions_per_game * games

        tov_pct = calculate_turnover_percentage(turnovers, total_possessions)
        if tov_pct:
            factors["turnover_percentage"] = tov_pct

        # Offensive Rebound Percentage
        orb = totals.get("total_offensive_rebounds", 0)
        orb_pct = calculate_offensive_rebound_percentage(orb, fga, fgm)
        if orb_pct:
            factors["offensive_rebound_percentage"] = orb_pct

        # Free Throw Rate
        fta = totals.get("total_free_throws_attempted", 0)
        ft_rate = calculate_free_throw_rate(fta, fga)
        if ft_rate:
            factors["free_throw_rate"] = ft_rate

        return factors

    def _calculate_shooting_metrics(self, totals: dict) -> dict:
        """Calculate shooting efficiency metrics."""
        metrics = {}

        # True Shooting Percentage
        points = totals.get("total_points", 0)
        fga = totals.get("total_field_goals_attempted", 0)
        fta = totals.get("total_free_throws_attempted", 0)

        ts_pct = calculate_true_shooting_percentage(points, fga, fta)
        if ts_pct:
            metrics["true_shooting_percentage"] = ts_pct

        # Basic shooting percentages
        fgm = totals.get("total_field_goals_made", 0)
        if fga > 0:
            metrics["field_goal_percentage"] = round(fgm / fga, 3)

        tpm = totals.get("total_three_pointers_made", 0)
        tpa = totals.get("total_three_pointers_attempted", 0)
        if tpa > 0:
            metrics["three_point_percentage"] = round(tpm / tpa, 3)

        ftm = totals.get("total_free_throws_made", 0)
        if fta > 0:
            metrics["free_throw_percentage"] = round(ftm / fta, 3)

        return metrics

    def _calculate_home_away_splits(self, df: "pd.DataFrame") -> dict:
        """Calculate home/away performance splits."""
        import pandas as pd

        splits = {"home": {}, "away": {}}

        if "is_home" in df.columns:
            for venue in ["home", "away"]:
                venue_df = df[df["is_home"] == (venue == "home")]
                if len(venue_df) > 0:
                    splits[venue] = {
                        "games": len(venue_df),
                        "wins": venue_df.get("win", pd.Series([False])).sum(),
                        "points_per_game": round(venue_df["points"].mean(), 1),
                        "points_allowed_per_game": round(
                            venue_df["points_allowed"].mean(), 1
                        ),
                    }
                    # Calculate win percentage
                    if splits[venue]["games"] > 0:
                        splits[venue]["win_percentage"] = round(
                            splits[venue]["wins"] / splits[venue]["games"], 3
                        )

        return splits

    def _calculate_monthly_splits(self, df: "pd.DataFrame") -> dict:
        """Calculate monthly performance splits."""
        splits = {}

        if "game_date" in df.columns:
            import pandas as pd

            # Convert game_date to datetime if it's not already
            df_copy = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_copy["game_date"]):
                df_copy["game_date"] = pd.to_datetime(df_copy["game_date"])

            # Group by month
            df_copy["month"] = df_copy["game_date"].dt.strftime("%Y-%m")

            for month, month_df in df_copy.groupby("month"):
                splits[month] = {
                    "games": len(month_df),
                    "wins": month_df.get("win", pd.Series([False])).sum(),
                    "points_per_game": round(month_df["points"].mean(), 1),
                    "points_allowed_per_game": round(
                        month_df["points_allowed"].mean(), 1
                    ),
                }
                # Calculate win percentage
                if splits[month]["games"] > 0:
                    splits[month]["win_percentage"] = round(
                        splits[month]["wins"] / splits[month]["games"], 3
                    )

        return splits

    def _calculate_data_quality_score(self, df: "pd.DataFrame") -> float:
        """Calculate overall data quality score for the season."""
        from .quality import calculate_data_quality_score

        # Calculate average data quality across all games
        quality_scores = []
        for _, game in df.iterrows():
            game_dict = game.to_dict()
            score = calculate_data_quality_score(game_dict)
            quality_scores.append(score)

        return (
            round(sum(quality_scores) / len(quality_scores), 3)
            if quality_scores
            else 0.0
        )

    def _count_games_with_missing_data(self, df: "pd.DataFrame") -> int:
        """Count games with significant missing data."""
        import pandas as pd

        critical_fields = ["points", "points_allowed", "field_goals_attempted"]
        missing_count = 0

        for _, game in df.iterrows():
            missing_critical = sum(
                1
                for field in critical_fields
                if game.get(field) is None or pd.isna(game.get(field))
            )
            if missing_critical >= 2:  # More than half of critical fields missing
                missing_count += 1

        return missing_count

    def _empty_season_stats(self, season: str, season_type: str) -> dict:
        """Return empty season stats structure for invalid data."""
        return {
            "season": season,
            "season_type": season_type,
            "total_games": 0,
            "data_quality_score": 0.0,
            "error": "Insufficient or invalid data for aggregation",
        }
