"""
Data validation utilities for the player daily aggregator.

This module provides validation functions for input and output data
to ensure data quality and integrity.
"""

import logging

import pandas as pd

from app.config import LambdaConfig

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""

    pass


def validate_input_data(df: pd.DataFrame, config: LambdaConfig) -> None:
    """
    Validate Silver layer input data.

    Args:
        df: Input DataFrame from Silver layer
        config: Lambda configuration with validation settings

    Raises:
        ValidationError: If validation fails
    """
    logger.info(f"Validating input data with {len(df)} rows")

    # Check if DataFrame is empty
    if len(df) == 0:
        raise ValidationError("Input DataFrame is empty")

    # Check for required columns
    required_columns = {
        "player_id",
        "points",
        "rebounds",
        "assists",
        "field_goals_made",
        "field_goals_attempted",
        "three_pointers_made",
        "three_pointers_attempted",
        "free_throws_made",
        "free_throws_attempted",
        "steals",
        "blocks",
        "turnovers",
        "minutes_played",
    }

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")

    # Check for minimum number of players
    unique_players = df["player_id"].nunique()
    if unique_players < config.min_expected_players:
        raise ValidationError(
            f"Too few players in data: {unique_players} < {config.min_expected_players}"
        )

    # Check for null values in critical columns
    for col in ["player_id", "points", "rebounds", "assists"]:
        null_percentage = df[col].isnull().sum() / len(df)
        if null_percentage > config.max_null_percentage:
            raise ValidationError(
                f"Too many null values in {col}: {null_percentage:.2%} > "
                f"{config.max_null_percentage:.2%}"
            )

    # Check for negative values in counting stats
    counting_stats = [
        "points",
        "rebounds",
        "assists",
        "field_goals_made",
        "field_goals_attempted",
        "three_pointers_made",
        "three_pointers_attempted",
        "free_throws_made",
        "free_throws_attempted",
        "steals",
        "blocks",
        "turnovers",
        "minutes_played",
    ]

    for col in counting_stats:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                raise ValidationError(
                    f"Found {negative_count} negative values in {col}"
                )

    # Check for impossible shooting stats (made > attempted)
    shooting_pairs = [
        ("field_goals_made", "field_goals_attempted"),
        ("three_pointers_made", "three_pointers_attempted"),
        ("free_throws_made", "free_throws_attempted"),
    ]

    for made_col, attempted_col in shooting_pairs:
        if made_col in df.columns and attempted_col in df.columns:
            impossible_count = (df[made_col] > df[attempted_col]).sum()
            if impossible_count > 0:
                raise ValidationError(
                    f"Found {impossible_count} records where "
                    f"{made_col} > {attempted_col}"
                )

    logger.info("Input data validation passed")


def validate_output_data(df: pd.DataFrame, config: LambdaConfig) -> None:
    """
    Validate Gold layer output data.

    Args:
        df: Output DataFrame for Gold layer
        config: Lambda configuration with validation settings

    Raises:
        ValidationError: If validation fails
    """
    logger.info(f"Validating output data with {len(df)} rows")

    # Check if DataFrame is empty
    if len(df) == 0:
        raise ValidationError("Output DataFrame is empty")

    # Check for required columns in output
    required_output_columns = {
        "player_id",
        "season",
        "points",
        "rebounds",
        "assists",
        "field_goal_percentage",
        "three_point_percentage",
        "free_throw_percentage",
    }

    missing_columns = required_output_columns - set(df.columns)
    if missing_columns:
        raise ValidationError(f"Missing required output columns: {missing_columns}")

    # Check percentage columns are between 0 and 1
    percentage_columns = [
        "field_goal_percentage",
        "three_point_percentage",
        "free_throw_percentage",
    ]

    for col in percentage_columns:
        if col in df.columns:
            # Allow NaN values but check non-null values are in valid range
            valid_values = df[col].dropna()
            if len(valid_values) > 0:
                if (valid_values < 0).any() or (valid_values > 1).any():
                    raise ValidationError(
                        f"Invalid percentage values in {col} (must be 0-1)"
                    )

    # Check for duplicate player IDs in daily stats (should be unique per day)
    if "date" in df.columns:
        # This is daily stats - check for duplicates within each date
        for date in df["date"].unique():
            date_df = df[df["date"] == date]
            duplicate_players = date_df["player_id"].duplicated().sum()
            if duplicate_players > 0:
                raise ValidationError(
                    f"Found {duplicate_players} duplicate players for date {date}"
                )
    else:
        # This is season stats - check for duplicates within each season
        for season in df["season"].unique():
            season_df = df[df["season"] == season]
            duplicate_players = season_df["player_id"].duplicated().sum()
            if duplicate_players > 0:
                raise ValidationError(
                    f"Found {duplicate_players} duplicate players for season {season}"
                )

    logger.info("Output data validation passed")


def validate_row_counts(input_df: pd.DataFrame, output_df: pd.DataFrame) -> None:
    """
    Validate that row counts are reasonable between input and output.

    Args:
        input_df: Input DataFrame
        output_df: Output DataFrame

    Raises:
        ValidationError: If row count validation fails
    """
    input_players = input_df["player_id"].nunique()
    output_players = len(output_df)

    # Output should have one row per unique player in input
    if output_players != input_players:
        raise ValidationError(
            f"Row count mismatch: {input_players} unique players in input, "
            f"{output_players} rows in output"
        )

    logger.info(
        f"Row count validation passed: {output_players} output rows for "
        f"{input_players} input players"
    )
