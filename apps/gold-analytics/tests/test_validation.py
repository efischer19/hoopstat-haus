"""Tests for the validation module."""

from datetime import date

import pandas as pd
import pytest

from app.validation import DataQualityError, DataValidator


class TestDataValidator:
    """Test cases for the DataValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization with different modes."""
        validator = DataValidator("strict")
        assert validator.validation_mode == "strict"

        validator = DataValidator("lenient")
        assert validator.validation_mode == "lenient"

    def test_validator_invalid_mode(self):
        """Test validator with invalid validation mode."""
        with pytest.raises(ValueError, match="Invalid validation_mode"):
            DataValidator("invalid_mode")

    def test_validate_silver_player_data_success(self):
        """Test successful validation of silver player data."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "team_id": ["team_1", "team_2"],
            "points": [25, 18],
            "rebounds": [8, 6],
            "assists": [5, 9],
            "field_goals_made": [10, 7],
            "field_goals_attempted": [18, 15],
            "minutes_played": [35, 32],
        })

        result = validator.validate_silver_player_data(df, date(2024, 1, 1))
        assert result is True

    def test_validate_silver_player_data_missing_columns(self):
        """Test validation with missing required columns."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "points": [25, 18],
            # Missing required columns
        })

        with pytest.raises(DataQualityError, match="Missing required columns"):
            validator.validate_silver_player_data(df, date(2024, 1, 1))

    def test_validate_silver_player_data_negative_values(self):
        """Test validation with negative values in statistics."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "team_id": ["team_1", "team_2"],
            "points": [-5, 18],  # Negative points
            "rebounds": [8, 6],
            "assists": [5, 9],
            "field_goals_made": [10, 7],
            "field_goals_attempted": [18, 15],
            "minutes_played": [35, 32],
        })

        with pytest.raises(DataQualityError, match="negative values in points"):
            validator.validate_silver_player_data(df, date(2024, 1, 1))

    def test_validate_silver_player_data_lenient_mode(self):
        """Test validation in lenient mode allows issues."""
        validator = DataValidator("lenient")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "team_id": ["team_1", "team_2"],
            "points": [-5, 18],  # Negative points
            "rebounds": [8, 6],
            "assists": [5, 9],
            "field_goals_made": [10, 7],
            "field_goals_attempted": [18, 15],
            "minutes_played": [35, 32],
        })

        # Should pass in lenient mode despite negative values
        result = validator.validate_silver_player_data(df, date(2024, 1, 1))
        assert result is True

    def test_validate_gold_analytics_player(self):
        """Test validation of gold player analytics."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "true_shooting_pct": [58.5, 62.1],
            "player_efficiency_rating": [22.5, 28.3],
            "usage_rate": [28.5, 32.1],
        })

        result = validator.validate_gold_analytics(df, "player")
        assert result is True

    def test_validate_gold_analytics_unrealistic_values(self):
        """Test validation with unrealistic analytics values."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1"],
            "usage_rate": [150.0],  # Unrealistic usage rate
        })

        with pytest.raises(DataQualityError, match="unrealistic usage rate"):
            validator.validate_gold_analytics(df, "player")

    def test_validate_data_consistency(self):
        """Test data consistency validation between silver and gold."""
        validator = DataValidator("strict")

        silver_df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "points": [25, 18],
        })

        gold_df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "points": [25, 18],
            "true_shooting_pct": [58.5, 62.1],
        })

        result = validator.validate_data_consistency(silver_df, gold_df, "player")
        assert result is True

    def test_validate_data_consistency_record_mismatch(self):
        """Test consistency validation with record count mismatch."""
        validator = DataValidator("strict")

        silver_df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "points": [25, 18],
        })

        gold_df = pd.DataFrame({
            "player_id": ["player_1"],  # Missing player_2
            "points": [25],
            "true_shooting_pct": [58.5],
        })

        with pytest.raises(DataQualityError, match="Record count mismatch"):
            validator.validate_data_consistency(silver_df, gold_df, "player")

    def test_validate_schema_compliance(self):
        """Test schema compliance validation."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            "points": [25, 18],
        })

        expected_schema = {
            "player_id": "string",
            "points": "int",
        }

        result = validator.validate_schema_compliance(df, expected_schema)
        assert result is True

    def test_validate_schema_compliance_missing_columns(self):
        """Test schema validation with missing columns."""
        validator = DataValidator("strict")

        df = pd.DataFrame({
            "player_id": ["player_1", "player_2"],
            # Missing points column
        })

        expected_schema = {
            "player_id": "string",
            "points": "int",
        }

        with pytest.raises(DataQualityError, match="Missing required columns"):
            validator.validate_schema_compliance(df, expected_schema)
