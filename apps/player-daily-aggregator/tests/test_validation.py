"""Test validation module."""

import pandas as pd
import pytest

from app.config import LambdaConfig
from app.validation import ValidationError, validate_input_data, validate_output_data


class TestValidation:
    """Test cases for data validation functions."""

    def test_validate_input_data_success(self):
        """Test successful input data validation."""
        # Create valid test data
        df = pd.DataFrame(
            {
                "player_id": ["player1", "player2", "player3"],
                "points": [25, 18, 12],
                "rebounds": [8, 6, 4],
                "assists": [5, 3, 2],
                "field_goals_made": [10, 7, 5],
                "field_goals_attempted": [20, 15, 12],
                "three_pointers_made": [3, 2, 1],
                "three_pointers_attempted": [8, 6, 4],
                "free_throws_made": [2, 2, 1],
                "free_throws_attempted": [2, 3, 2],
                "steals": [2, 1, 0],
                "blocks": [1, 0, 1],
                "turnovers": [3, 2, 1],
                "minutes_played": [35, 28, 22],
            }
        )

        config = LambdaConfig(
            silver_bucket="test",
            gold_bucket="test",
            min_expected_players=1,
            max_null_percentage=0.1,
        )

        # Should not raise any exception
        validate_input_data(df, config)

    def test_validate_input_data_empty_dataframe(self):
        """Test validation fails for empty DataFrame."""
        df = pd.DataFrame()
        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        with pytest.raises(ValidationError, match="Input DataFrame is empty"):
            validate_input_data(df, config)

    def test_validate_input_data_missing_columns(self):
        """Test validation fails for missing required columns."""
        df = pd.DataFrame(
            {
                "player_id": ["player1"],
                "points": [25],
                # Missing other required columns
            }
        )
        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        with pytest.raises(ValidationError, match="Missing required columns"):
            validate_input_data(df, config)

    def test_validate_input_data_too_few_players(self):
        """Test validation fails when too few players."""
        df = pd.DataFrame(
            {
                "player_id": ["player1"],
                "points": [25],
                "rebounds": [8],
                "assists": [5],
                "field_goals_made": [10],
                "field_goals_attempted": [20],
                "three_pointers_made": [3],
                "three_pointers_attempted": [8],
                "free_throws_made": [2],
                "free_throws_attempted": [2],
                "steals": [2],
                "blocks": [1],
                "turnovers": [3],
                "minutes_played": [35],
            }
        )

        config = LambdaConfig(
            silver_bucket="test",
            gold_bucket="test",
            min_expected_players=5,  # Require more players than we have
        )

        with pytest.raises(ValidationError, match="Too few players in data"):
            validate_input_data(df, config)

    def test_validate_input_data_too_many_nulls(self):
        """Test validation fails when too many null values."""
        df = pd.DataFrame(
            {
                "player_id": ["player1", "player2", None, None],  # 50% nulls
                "points": [25, 18, 12, 8],
                "rebounds": [8, 6, 4, 3],
                "assists": [5, 3, 2, 1],
                "field_goals_made": [10, 7, 5, 3],
                "field_goals_attempted": [20, 15, 12, 8],
                "three_pointers_made": [3, 2, 1, 0],
                "three_pointers_attempted": [8, 6, 4, 2],
                "free_throws_made": [2, 2, 1, 1],
                "free_throws_attempted": [2, 3, 2, 1],
                "steals": [2, 1, 0, 1],
                "blocks": [1, 0, 1, 0],
                "turnovers": [3, 2, 1, 2],
                "minutes_played": [35, 28, 22, 18],
            }
        )

        config = LambdaConfig(
            silver_bucket="test",
            gold_bucket="test",
            max_null_percentage=0.1,  # Only allow 10% nulls, but we have 50%
        )

        with pytest.raises(ValidationError, match="Too many null values"):
            validate_input_data(df, config)

    def test_validate_input_data_negative_values(self):
        """Test validation fails for negative values in counting stats."""
        df = pd.DataFrame(
            {
                "player_id": ["player1"],
                "points": [-5],  # Negative points should fail
                "rebounds": [8],
                "assists": [5],
                "field_goals_made": [10],
                "field_goals_attempted": [20],
                "three_pointers_made": [3],
                "three_pointers_attempted": [8],
                "free_throws_made": [2],
                "free_throws_attempted": [2],
                "steals": [2],
                "blocks": [1],
                "turnovers": [3],
                "minutes_played": [35],
            }
        )

        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        with pytest.raises(ValidationError, match="negative values in points"):
            validate_input_data(df, config)

    def test_validate_input_data_impossible_shooting(self):
        """Test validation fails when made > attempted for shooting stats."""
        df = pd.DataFrame(
            {
                "player_id": ["player1"],
                "points": [25],
                "rebounds": [8],
                "assists": [5],
                "field_goals_made": [15],  # Made more than attempted
                "field_goals_attempted": [10],
                "three_pointers_made": [3],
                "three_pointers_attempted": [8],
                "free_throws_made": [2],
                "free_throws_attempted": [2],
                "steals": [2],
                "blocks": [1],
                "turnovers": [3],
                "minutes_played": [35],
            }
        )

        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        with pytest.raises(
            ValidationError, match="field_goals_made > field_goals_attempted"
        ):
            validate_input_data(df, config)

    def test_validate_output_data_success(self):
        """Test successful output data validation."""
        df = pd.DataFrame(
            {
                "player_id": ["player1", "player2"],
                "season": ["2023-24", "2023-24"],
                "points": [25, 18],
                "rebounds": [8, 6],
                "assists": [5, 3],
                "field_goal_percentage": [0.5, 0.47],
                "three_point_percentage": [0.375, 0.33],
                "free_throw_percentage": [1.0, 0.67],
            }
        )

        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        # Should not raise any exception
        validate_output_data(df, config)

    def test_validate_output_data_invalid_percentages(self):
        """Test validation fails for invalid percentage values."""
        df = pd.DataFrame(
            {
                "player_id": ["player1"],
                "season": ["2023-24"],
                "points": [25],
                "rebounds": [8],
                "assists": [5],
                "field_goal_percentage": [1.5],  # Invalid percentage > 1
                "three_point_percentage": [0.375],
                "free_throw_percentage": [1.0],
            }
        )

        config = LambdaConfig(silver_bucket="test", gold_bucket="test")

        with pytest.raises(ValidationError, match="Invalid percentage values"):
            validate_output_data(df, config)
