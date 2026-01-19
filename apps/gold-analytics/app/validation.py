"""
Data validation and quality checks for Gold Analytics.

This module provides validation functions to ensure data quality
and consistency throughout the processing pipeline.
"""

from datetime import date

import pandas as pd
from hoopstat_observability import get_logger

logger = get_logger(__name__)


class DataQualityError(Exception):
    """Exception raised when data quality checks fail."""

    pass


class DataValidator:
    """
    Validator for Silver and Gold layer data quality checks.

    Provides comprehensive validation of data consistency, completeness,
    and correctness throughout the analytics pipeline.
    """

    def __init__(self, validation_mode: str = "strict") -> None:
        """
        Initialize data validator.

        Args:
            validation_mode: Validation strictness ("strict", "lenient", "warn_only")
        """
        if validation_mode not in ["strict", "lenient", "warn_only"]:
            raise ValueError(f"Invalid validation_mode: {validation_mode}")

        self.validation_mode = validation_mode
        logger.info(f"Initialized DataValidator with mode: {validation_mode}")

    def validate_silver_player_data(self, df: pd.DataFrame, target_date: date) -> bool:
        """
        Validate Silver layer player statistics data.

        Args:
            df: DataFrame containing player statistics
            target_date: Expected date for the data

        Returns:
            True if validation passes

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        issues = []

        # Check required columns
        required_columns = [
            "player_id",
            "points",
            "rebounds",
            "assists",
            "field_goals_made",
            "field_goals_attempted",
            "minutes_played",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")

        if "team_id" not in df.columns and "team" not in df.columns:
            issues.append("Missing required team identifier: team_id or team")

        if df.empty:
            issues.append("DataFrame is empty")
        else:
            # Check for duplicate player records
            if "player_id" in df.columns:
                duplicates = df.duplicated(subset=["player_id"]).sum()
                if duplicates > 0:
                    issues.append(f"Found {duplicates} duplicate player records")

            # Check for negative values in statistics
            numeric_columns = [
                "points",
                "rebounds",
                "assists",
                "field_goals_made",
                "field_goals_attempted",
            ]
            for col in numeric_columns:
                if col in df.columns:
                    negative_count = (df[col] < 0).sum()
                    if negative_count > 0:
                        issues.append(
                            f"Found {negative_count} negative values in {col}"
                        )

            # Check field goal logic (made <= attempted)
            if (
                "field_goals_made" in df.columns
                and "field_goals_attempted" in df.columns
            ):
                invalid_fg = (
                    df["field_goals_made"] > df["field_goals_attempted"]
                ).sum()
                if invalid_fg > 0:
                    issues.append(
                        f"Found {invalid_fg} records where FG made > FG attempted"
                    )

            # Check minutes played (should be reasonable)
            if "minutes_played" in df.columns:
                invalid_minutes = (df["minutes_played"] > 48).sum()
                if invalid_minutes > 0:
                    issues.append(
                        f"Found {invalid_minutes} records with >48 minutes played"
                    )

        return self._handle_validation_issues(issues, "silver_player_data", target_date)

    def validate_silver_team_data(self, df: pd.DataFrame, target_date: date) -> bool:
        """
        Validate Silver layer team statistics data.

        Args:
            df: DataFrame containing team statistics
            target_date: Expected date for the data

        Returns:
            True if validation passes

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        issues = []

        # Check required columns
        required_columns = [
            "team_id",
            "points",
            "field_goals_made",
            "field_goals_attempted",
            "rebounds",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")

        if df.empty:
            issues.append("DataFrame is empty")
        else:
            # Check for duplicate team records
            if "team_id" in df.columns:
                duplicates = df.duplicated(subset=["team_id"]).sum()
                if duplicates > 0:
                    issues.append(f"Found {duplicates} duplicate team records")

            # Check for negative values in statistics
            numeric_columns = [
                "points",
                "field_goals_made",
                "field_goals_attempted",
                "rebounds",
            ]
            for col in numeric_columns:
                if col in df.columns:
                    negative_count = (df[col] < 0).sum()
                    if negative_count > 0:
                        issues.append(
                            f"Found {negative_count} negative values in {col}"
                        )

            # Check field goal logic
            if (
                "field_goals_made" in df.columns
                and "field_goals_attempted" in df.columns
            ):
                invalid_fg = (
                    df["field_goals_made"] > df["field_goals_attempted"]
                ).sum()
                if invalid_fg > 0:
                    issues.append(
                        f"Found {invalid_fg} records where FG made > FG attempted"
                    )

        return self._handle_validation_issues(issues, "silver_team_data", target_date)

    def validate_gold_analytics(self, df: pd.DataFrame, data_type: str) -> bool:
        """
        Validate Gold layer analytics data.

        Args:
            df: DataFrame containing analytics data
            data_type: Type of analytics ("player" or "team")

        Returns:
            True if validation passes

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        issues = []

        if df.empty:
            issues.append("Analytics DataFrame is empty")
            return self._handle_validation_issues(issues, f"gold_{data_type}_analytics")

        # Check for null values in key metrics
        if data_type == "player":
            key_metrics = [
                "true_shooting_pct",
                "player_efficiency_rating",
                "usage_rate",
            ]
        else:  # team
            key_metrics = ["offensive_rating", "defensive_rating", "net_rating"]

        for metric in key_metrics:
            if metric in df.columns:
                null_count = df[metric].isnull().sum()
                if null_count > 0:
                    issues.append(f"Found {null_count} null values in {metric}")

        # Check for unrealistic values
        if data_type == "player":
            # Usage rate should be between 0 and 50%
            if "usage_rate" in df.columns:
                invalid_usage = ((df["usage_rate"] < 0) | (df["usage_rate"] > 50)).sum()
                if invalid_usage > 0:
                    issues.append(
                        f"Found {invalid_usage} unrealistic usage rate values"
                    )

            # True shooting percentage should be between 0 and 100%
            if "true_shooting_pct" in df.columns:
                invalid_ts = (
                    (df["true_shooting_pct"] < 0) | (df["true_shooting_pct"] > 100)
                ).sum()
                if invalid_ts > 0:
                    issues.append(
                        f"Found {invalid_ts} unrealistic true shooting "
                        f"percentage values"
                    )

        else:  # team
            # Net rating should be reasonable (-50 to +50)
            if "net_rating" in df.columns:
                invalid_net = ((df["net_rating"] < -50) | (df["net_rating"] > 50)).sum()
                if invalid_net > 0:
                    issues.append(f"Found {invalid_net} unrealistic net rating values")

        return self._handle_validation_issues(issues, f"gold_{data_type}_analytics")

    def validate_data_consistency(
        self, silver_df: pd.DataFrame, gold_df: pd.DataFrame, data_type: str
    ) -> bool:
        """
        Validate consistency between Silver and Gold layer data.

        Args:
            silver_df: Original Silver layer data
            gold_df: Processed Gold layer analytics
            data_type: Type of data ("player" or "team")

        Returns:
            True if consistency checks pass

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        issues = []

        # Check record count consistency
        if len(silver_df) != len(gold_df):
            issues.append(
                f"Record count mismatch: Silver has {len(silver_df)} records, "
                f"Gold has {len(gold_df)} records"
            )

        # Check that no records were lost during processing
        if (
            data_type == "player"
            and "player_id" in silver_df.columns
            and "player_id" in gold_df.columns
        ):
            silver_ids = set(silver_df["player_id"])
            gold_ids = set(gold_df["player_id"])

            missing_ids = silver_ids - gold_ids
            if missing_ids:
                issues.append(f"Lost {len(missing_ids)} player IDs during processing")

            extra_ids = gold_ids - silver_ids
            if extra_ids:
                issues.append(
                    f"Added {len(extra_ids)} unexpected player IDs during processing"
                )

        elif (
            data_type == "team"
            and "team_id" in silver_df.columns
            and "team_id" in gold_df.columns
        ):
            silver_ids = set(silver_df["team_id"])
            gold_ids = set(gold_df["team_id"])

            missing_ids = silver_ids - gold_ids
            if missing_ids:
                issues.append(f"Lost {len(missing_ids)} team IDs during processing")

            extra_ids = gold_ids - silver_ids
            if extra_ids:
                issues.append(
                    f"Added {len(extra_ids)} unexpected team IDs during processing"
                )

        return self._handle_validation_issues(issues, f"{data_type}_consistency")

    def validate_schema_compliance(
        self, df: pd.DataFrame, expected_schema: dict[str, str]
    ) -> bool:
        """
        Validate that DataFrame schema matches expected schema.

        Args:
            df: DataFrame to validate
            expected_schema: Dictionary mapping column names to expected data types

        Returns:
            True if schema is compliant

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        issues = []

        # Check for missing required columns
        missing_columns = set(expected_schema.keys()) - set(df.columns)
        if missing_columns:
            issues.append(f"Missing required columns: {list(missing_columns)}")

        # Check data types
        for column, expected_type in expected_schema.items():
            if column in df.columns:
                actual_type = str(df[column].dtype)
                if not self._is_compatible_type(actual_type, expected_type):
                    issues.append(
                        f"Column {column} has type {actual_type}, "
                        f"expected {expected_type}"
                    )

        return self._handle_validation_issues(issues, "schema_compliance")

    def _is_compatible_type(self, actual: str, expected: str) -> bool:
        """Check if actual data type is compatible with expected type."""
        # Define type compatibility mappings
        compatible_types = {
            "int64": ["int", "integer", "int64", "int32"],
            "float64": ["float", "float64", "float32", "numeric"],
            "object": ["string", "object", "str"],
            "bool": ["boolean", "bool"],
            "datetime64[ns]": ["datetime", "timestamp"],
        }

        for actual_base, compatible_list in compatible_types.items():
            if actual.startswith(actual_base) and expected.lower() in compatible_list:
                return True

        return False

    def _handle_validation_issues(
        self,
        issues: list[str],
        validation_type: str,
        target_date: date | None = None,
    ) -> bool:
        """
        Handle validation issues based on validation mode.

        Args:
            issues: List of validation issues found
            validation_type: Type of validation being performed
            target_date: Date being validated (optional)

        Returns:
            True if validation passes or is in lenient mode

        Raises:
            DataQualityError: If validation fails in strict mode
        """
        if not issues:
            logger.info(f"Validation passed: {validation_type}")
            return True

        date_str = f" for {target_date}" if target_date else ""
        issue_summary = (
            f"Validation issues in {validation_type}{date_str}: {'; '.join(issues)}"
        )

        if self.validation_mode == "strict":
            logger.error(issue_summary)
            raise DataQualityError(issue_summary)
        elif self.validation_mode == "lenient":
            logger.warning(f"Lenient mode - continuing despite issues: {issue_summary}")
            return True
        else:  # warn_only
            logger.warning(f"Warning only - {issue_summary}")
            return True


def get_expected_player_schema() -> dict[str, str]:
    """Get expected schema for player analytics data."""
    return {
        "player_id": "string",
        "team_id": "string",
        "points": "int",
        "rebounds": "int",
        "assists": "int",
        "true_shooting_pct": "float",
        "player_efficiency_rating": "float",
        "usage_rate": "float",
        "offensive_rating": "float",
    }


def get_expected_team_schema() -> dict[str, str]:
    """Get expected schema for team analytics data."""
    return {
        "team_id": "string",
        "points": "int",
        "offensive_rating": "float",
        "defensive_rating": "float",
        "net_rating": "float",
        "pace": "float",
        "effective_field_goal_pct": "float",
    }
