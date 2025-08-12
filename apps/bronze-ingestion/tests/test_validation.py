"""Tests for the validation module."""

from datetime import date

import jsonschema
import pytest

from app.schemas import get_schema
from app.validation import DataValidator


class TestSchemas:
    """Test JSON schema definitions."""

    def test_get_schema_valid_types(self):
        """Test that valid schema types return proper schemas."""
        schedule_schema = get_schema("schedule")
        assert schedule_schema["type"] == "array"

        box_score_schema = get_schema("box_score")
        assert box_score_schema["type"] == "object"
        assert "resultSets" in box_score_schema["required"]

    def test_get_schema_invalid_type(self):
        """Test that invalid schema types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported response type"):
            get_schema("invalid_type")

    def test_schedule_schema_validation(self):
        """Test schedule schema validation with valid data."""
        schema = get_schema("schedule")

        # Valid schedule data
        valid_data = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 123,
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "PTS": 110,
            }
        ]

        # Should not raise any exception
        jsonschema.validate(valid_data, schema)

    def test_schedule_schema_validation_invalid(self):
        """Test schedule schema validation with invalid data."""
        schema = get_schema("schedule")

        # Invalid data - missing required fields
        invalid_data = [
            {
                "GAME_ID": "123",  # Too short
                "TEAM_ABBREVIATION": "LAL",
                # Missing GAME_DATE and TEAM_ID
            }
        ]

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_data, schema)

    def test_box_score_schema_validation(self):
        """Test box score schema validation with valid data."""
        schema = get_schema("box_score")

        # Valid box score data
        valid_data = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "MIN", "PTS"],
                    "rowSet": [
                        ["123", "LeBron James", 35, 25],
                        ["456", "Anthony Davis", 30, 20],
                    ],
                }
            ],
            "parameters": {
                "GameID": "1234567890",
            },
        }

        # Should not raise any exception
        jsonschema.validate(valid_data, schema)


class TestDataValidator:
    """Test the DataValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def test_validate_api_response_valid_schedule(self):
        """Test validation of valid schedule data."""
        valid_schedule = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 123,
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
                "PTS": 110,
            }
        ]

        result = self.validator.validate_api_response(
            valid_schedule, "schedule", {"target_date": date(2023, 12, 25)}
        )

        assert result["valid"] is True
        assert result["metrics"]["schema_valid"] is True
        assert result["metrics"]["game_count"] == 1
        assert len(result["issues"]) == 0

    def test_validate_api_response_invalid_schedule(self):
        """Test validation of invalid schedule data."""
        invalid_schedule = [
            {
                "GAME_ID": "123",  # Too short
                "GAME_DATE": "invalid-date",
                # Missing required TEAM_ID
            }
        ]

        result = self.validator.validate_api_response(invalid_schedule, "schedule")

        assert result["valid"] is False
        assert result["metrics"]["schema_valid"] is False
        assert len(result["issues"]) > 0
        assert any("Schema validation failed" in issue for issue in result["issues"])

    def test_validate_api_response_valid_box_score(self):
        """Test validation of valid box score data."""
        valid_box_score = {
            "resultSets": [
                {
                    "name": "PlayerStats",
                    "headers": ["PLAYER_ID", "PLAYER_NAME", "PTS"],
                    "rowSet": [
                        ["123", "LeBron James", 25],
                    ],
                }
            ],
            "parameters": {
                "GameID": "1234567890",
            },
        }

        result = self.validator.validate_api_response(valid_box_score, "box_score")

        assert result["valid"] is True
        assert result["metrics"]["schema_valid"] is True
        assert result["metrics"]["result_set_count"] == 1

    def test_validate_completeness_sufficient_data(self):
        """Test completeness validation with sufficient data."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        result = self.validator.validate_completeness(
            data, expected_count=3, context="test_data"
        )

        assert result["complete"] is True
        assert result["actual_count"] == 3
        assert result["expected_count"] == 3
        assert len(result["issues"]) == 0

    def test_validate_completeness_insufficient_data(self):
        """Test completeness validation with insufficient data."""
        data = [{"id": 1}]

        result = self.validator.validate_completeness(
            data, expected_count=3, context="test_data"
        )

        assert result["complete"] is False
        assert result["actual_count"] == 1
        assert result["expected_count"] == 3
        assert len(result["issues"]) > 0

    def test_validate_completeness_empty_data(self):
        """Test completeness validation with empty data."""
        data = []

        result = self.validator.validate_completeness(
            data, expected_count=1, context="test_data"
        )

        assert result["complete"] is False
        assert result["actual_count"] == 0
        assert any("No data found" in issue for issue in result["issues"])

    def test_date_consistency_validation(self):
        """Test date consistency validation."""
        target_date = date(2023, 12, 25)
        schedule_data = [
            {
                "GAME_ID": "1234567890",
                "GAME_DATE": "2023-12-25",
                "TEAM_ID": 123,
                "PTS": 110,
            },
            {
                "GAME_ID": "1234567891",
                "GAME_DATE": "2023-12-26",  # Wrong date
                "TEAM_ID": 124,
                "PTS": 105,
            },
        ]

        result = self.validator.validate_api_response(
            schedule_data, "schedule", {"target_date": target_date}
        )

        # Should have date consistency issues
        assert any("Date inconsistencies" in issue for issue in result["issues"])
        assert result["metrics"]["date_consistency"] is False

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        data = {
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "field_goals_made": 10,
            "field_goals_attempted": 15,
        }

        score = self.validator.calculate_quality_score(data)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_individual_game_validation(self):
        """Test individual game validation logic."""
        result = {"issues": [], "metrics": {}}

        # Valid game
        valid_game = {
            "GAME_ID": "1234567890",
            "PTS": 110,
        }

        is_valid = self.validator._validate_individual_game(
            valid_game, result, "test_game"
        )

        assert is_valid is True

        # Invalid game with unrealistic points
        invalid_game = {
            "GAME_ID": "1234567890",
            "PTS": 250,  # Unrealistic
        }

        result = {"issues": [], "metrics": {}}
        is_valid = self.validator._validate_individual_game(
            invalid_game, result, "test_game"
        )

        assert is_valid is False
        assert any("Unrealistic points value" in issue for issue in result["issues"])
