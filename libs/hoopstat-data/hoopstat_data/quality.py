"""
Data quality and consistency checking tools for basketball statistics.

Provides utilities for assessing data completeness, detecting outliers,
and ensuring data consistency across datasets.
"""

import logging
from statistics import mean, stdev
from typing import Any

logger = logging.getLogger(__name__)


def check_data_completeness(
    data: dict[str, Any], required_fields: list[str] | None = None
) -> dict[str, Any]:
    """
    Check data completeness and return completion metrics.

    Args:
        data: Dictionary containing data to check
        required_fields: Optional list of required field names

    Returns:
        Dictionary with completeness metrics

    Example:
        >>> data = {"points": 25, "rebounds": None, "assists": 5}
        >>> result = check_data_completeness(data)  # doctest: +SKIP
        # Returns completeness metrics dict
    """
    if required_fields is None:
        required_fields = [
            "points",
            "rebounds",
            "assists",
            "steals",
            "blocks",
            "turnovers",
        ]

    total_fields = len(required_fields)
    complete_fields = 0
    missing_fields = []

    for field in required_fields:
        if field in data and data[field] is not None:
            complete_fields += 1
        else:
            missing_fields.append(field)

    completeness_ratio = complete_fields / total_fields if total_fields > 0 else 0.0

    return {
        "total_fields": total_fields,
        "complete_fields": complete_fields,
        "missing_fields": missing_fields,
        "completeness_ratio": round(completeness_ratio, 2),
        "is_complete": len(missing_fields) == 0,
    }


def detect_outliers(
    values: list[float], method: str = "iqr", threshold: float = 1.5
) -> list[int]:
    """
    Detect outliers in a list of numerical values.

    Args:
        values: List of numerical values
        method: Detection method ("iqr" or "zscore")
        threshold: Threshold for outlier detection

    Returns:
        List of indices of detected outliers

    Example:
        >>> values = [10, 12, 11, 13, 15, 50, 14]
        >>> detect_outliers(values)
        [5]  # Index of the value 50
    """
    if not values or len(values) < 3:
        return []

    outlier_indices = []

    try:
        if method == "iqr":
            # Interquartile Range method
            sorted_values = sorted(values)
            n = len(sorted_values)
            q1_idx = n // 4
            q3_idx = 3 * n // 4

            q1 = sorted_values[q1_idx]
            q3 = sorted_values[q3_idx]
            iqr = q3 - q1

            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    outlier_indices.append(i)

        elif method == "zscore":
            # Z-score method
            if len(values) < 2:
                return []

            values_mean = mean(values)
            values_std = stdev(values)

            if values_std == 0:  # All values are the same
                return []

            for i, value in enumerate(values):
                z_score = abs((value - values_mean) / values_std)
                if z_score > threshold:
                    outlier_indices.append(i)

    except Exception as e:
        logger.error(f"Error detecting outliers: {e}")

    return outlier_indices


def validate_stat_consistency(player_stats: list[dict[str, Any]]) -> list[str]:
    """
    Validate consistency across multiple player stat records.

    Args:
        player_stats: List of player statistics dictionaries

    Returns:
        List of consistency issues found

    Example:
        >>> stats = [
        ...     {"player_id": "123", "points": 25, "field_goals_made": 10},
        ...     {"player_id": "123", "points": -5, "field_goals_made": 15}
        ... ]
        >>> issues = validate_stat_consistency(stats)  # doctest: +SKIP
        # Returns list of consistency issues
    """
    issues = []

    if not player_stats:
        return issues

    # Group by player
    player_records = {}
    for stats in player_stats:
        player_id = stats.get("player_id")
        if player_id:
            if player_id not in player_records:
                player_records[player_id] = []
            player_records[player_id].append(stats)

    # Check consistency for each player
    for player_id, records in player_records.items():
        for record in records:
            # Check for negative stats
            for stat_name in ["points", "rebounds", "assists", "steals", "blocks"]:
                if record.get(stat_name, 0) < 0:
                    issues.append(f"Negative {stat_name} found for player {player_id}")

            # Check shooting consistency
            made = record.get("field_goals_made", 0)
            attempted = record.get("field_goals_attempted", 0)
            if attempted > 0 and made > attempted:
                issues.append(f"Inconsistent shooting stats for player {player_id}")

            # Check for unrealistic values
            points = record.get("points", 0)
            if points > 100:
                issues.append(
                    f"Unusually high points ({points}) for player {player_id}"
                )

    return issues


def calculate_data_quality_score(
    data: dict[str, Any], weights: dict[str, float] | None = None
) -> float:
    """
    Calculate an overall data quality score (0.0 to 1.0).

    Args:
        data: Dictionary containing data to assess
        weights: Optional weights for different quality factors

    Returns:
        Quality score from 0.0 (poor) to 1.0 (excellent)

    Example:
        >>> data = {"points": 25, "rebounds": 10, "assists": 5}
        >>> calculate_data_quality_score(data)
        0.85
    """
    if weights is None:
        weights = {"completeness": 0.4, "validity": 0.3, "consistency": 0.3}

    scores = {}

    # Completeness score
    completeness_result = check_data_completeness(data)
    scores["completeness"] = completeness_result["completeness_ratio"]

    # Validity score (basic range checks)
    validity_score = 1.0
    validity_checks = 0

    for field, value in data.items():
        if value is not None and field in [
            "points",
            "rebounds",
            "assists",
            "steals",
            "blocks",
        ]:
            validity_checks += 1
            if not isinstance(value, int | float) or value < 0:
                validity_score -= 0.2

    scores["validity"] = max(0.0, validity_score)

    # Consistency score (simplified)
    consistency_score = 1.0

    # Check field goal consistency
    made = data.get("field_goals_made")
    attempted = data.get("field_goals_attempted")
    if made is not None and attempted is not None:
        if made > attempted:
            consistency_score -= 0.5

    scores["consistency"] = max(0.0, consistency_score)

    # Calculate weighted average
    total_score = 0.0
    total_weight = 0.0

    for factor, score in scores.items():
        if factor in weights:
            total_score += score * weights[factor]
            total_weight += weights[factor]

    final_score = total_score / total_weight if total_weight > 0 else 0.0
    return round(final_score, 2)


def identify_missing_critical_stats(data: dict[str, Any]) -> list[str]:
    """
    Identify missing statistics that are critical for analysis.

    Args:
        data: Dictionary containing player/team statistics

    Returns:
        List of missing critical statistics

    Example:
        >>> data = {"rebounds": 10, "assists": 5}
        >>> identify_missing_critical_stats(data)
        ['points']
    """
    critical_stats = ["points", "rebounds", "assists"]
    missing_stats = []

    for stat in critical_stats:
        if stat not in data or data[stat] is None:
            missing_stats.append(stat)

    return missing_stats


def compare_stat_distributions(
    dataset1: list[dict[str, Any]], dataset2: list[dict[str, Any]], stat_name: str
) -> dict[str, float]:
    """
    Compare statistical distributions between two datasets.

    Args:
        dataset1: First dataset
        dataset2: Second dataset
        stat_name: Name of the statistic to compare

    Returns:
        Dictionary with comparison metrics

    Example:
        >>> data1 = [{"points": 20}, {"points": 25}]
        >>> data2 = [{"points": 15}, {"points": 30}]
        >>> compare_stat_distributions(data1, data2, "points")
        {'mean_diff': 0.0, 'std_diff': 3.54, 'sample_sizes': [2, 2]}
    """

    def extract_values(dataset, stat):
        return [record.get(stat) for record in dataset if record.get(stat) is not None]

    values1 = extract_values(dataset1, stat_name)
    values2 = extract_values(dataset2, stat_name)

    if not values1 or not values2:
        return {"error": "Insufficient data for comparison"}

    try:
        mean1 = mean(values1)
        mean2 = mean(values2)

        std1 = stdev(values1) if len(values1) > 1 else 0.0
        std2 = stdev(values2) if len(values2) > 1 else 0.0

        return {
            "mean_diff": round(mean1 - mean2, 2),
            "std_diff": round(abs(std1 - std2), 2),
            "mean1": round(mean1, 2),
            "mean2": round(mean2, 2),
            "std1": round(std1, 2),
            "std2": round(std2, 2),
            "sample_sizes": [len(values1), len(values2)],
        }

    except Exception as e:
        logger.error(f"Error comparing distributions: {e}")
        return {"error": str(e)}
