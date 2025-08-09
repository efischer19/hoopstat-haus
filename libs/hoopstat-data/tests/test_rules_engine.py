"""Tests for the data cleaning rules engine."""

from hoopstat_data.rules_engine import DataCleaningRulesEngine, TransformationResult


class TestDataCleaningRulesEngine:
    """Test cases for the DataCleaningRulesEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DataCleaningRulesEngine()

    def test_standardize_team_name_direct_mapping(self):
        """Test team name standardization with direct mappings."""
        result = self.engine.standardize_team_name("la lakers")
        assert result.success
        assert result.transformed_value == "Los Angeles Lakers"
        assert "direct_mapping" in result.applied_rules

    def test_standardize_team_name_fuzzy_matching(self):
        """Test team name standardization with fuzzy matching."""
        result = self.engine.standardize_team_name("Laker")  # Close to Lakers
        assert result.success
        # Should find a fuzzy match to "Los Angeles Lakers"
        assert "Lakers" in result.transformed_value

    def test_standardize_team_name_invalid_input(self):
        """Test team name standardization with invalid input."""
        result = self.engine.standardize_team_name("")
        assert not result.success
        assert result.error_message == "Invalid input"

        result = self.engine.standardize_team_name(None)
        assert not result.success

    def test_standardize_position_direct_mapping(self):
        """Test position standardization with direct mappings."""
        result = self.engine.standardize_position("Point Guard")
        assert result.success
        assert result.transformed_value == "PG"
        assert "direct_mapping" in result.applied_rules

    def test_standardize_position_partial_mapping(self):
        """Test position standardization with partial matching."""
        result = self.engine.standardize_position("Point Guard / Shooting Guard")
        assert result.success
        assert result.transformed_value == "PG"  # Should match first occurrence
        assert "partial_mapping" in result.applied_rules

    def test_standardize_position_unknown(self):
        """Test position standardization with unknown position."""
        result = self.engine.standardize_position("Unknown Position")
        assert result.success
        assert result.transformed_value == "UNKNOWN"
        assert "unknown_fallback" in result.applied_rules

    def test_handle_null_values(self):
        """Test null value handling."""
        data = {"player_id": "123", "points": 25, "rebounds": None, "assists": 5}

        cleaned = self.engine.handle_null_values(data, "player_stats")

        # Required fields should remain
        assert cleaned["player_id"] == "123"
        assert cleaned["points"] == 25
        assert cleaned["assists"] == 5

        # Null field should get default value
        assert cleaned["rebounds"] is None  # rebounds allows null

    def test_clean_numeric_field_valid(self):
        """Test numeric field cleaning with valid values."""
        result = self.engine.clean_numeric_field(25, "points")
        assert result.success
        assert result.transformed_value == 25.0

    def test_clean_numeric_field_string_conversion(self):
        """Test numeric field cleaning with string conversion."""
        result = self.engine.clean_numeric_field("25", "points")
        assert result.success
        assert result.transformed_value == 25.0
        assert "string_to_numeric" in result.applied_rules

    def test_clean_numeric_field_format_cleaning(self):
        """Test numeric field cleaning with format cleaning."""
        result = self.engine.clean_numeric_field(
            "$25", "points"
        )  # Use a value within range
        assert result.success
        assert result.transformed_value == 25.0
        assert "format_cleaning" in result.applied_rules

    def test_clean_numeric_field_range_validation(self):
        """Test numeric field cleaning with range validation."""
        # Test above maximum
        result = self.engine.clean_numeric_field(150, "points")  # Max is 100
        assert not result.success
        assert "above maximum" in result.error_message

        # Test below minimum
        result = self.engine.clean_numeric_field(-5, "points")  # Min is 0
        assert not result.success
        assert "below minimum" in result.error_message

    def test_standardize_datetime_iso_format(self):
        """Test datetime standardization with ISO format."""
        result = self.engine.standardize_datetime("2023-12-25T15:30:00Z")
        assert result.success
        assert "2023-12-25" in result.transformed_value

    def test_standardize_datetime_various_formats(self):
        """Test datetime standardization with various formats."""
        test_dates = [
            "2023-12-25",
            "12/25/2023",
            "2023-12-25 15:30:00",
        ]

        for date_str in test_dates:
            result = self.engine.standardize_datetime(date_str)
            assert result.success, f"Failed to parse date: {date_str}"
            assert "2023-12-25" in result.transformed_value

    def test_standardize_datetime_invalid(self):
        """Test datetime standardization with invalid input."""
        result = self.engine.standardize_datetime("invalid date")
        assert not result.success
        assert "Unable to parse datetime" in result.error_message

    def test_apply_fuzzy_matching(self):
        """Test fuzzy string matching."""
        candidates = ["Los Angeles Lakers", "Boston Celtics", "Chicago Bulls"]

        # Test good match
        result = self.engine.apply_fuzzy_matching("LA Lakers", candidates, "team_name")
        assert result.success
        assert result.transformed_value == "Los Angeles Lakers"

        # Test poor match
        result = self.engine.apply_fuzzy_matching("XYZ Team", candidates, "team_name")
        assert result.success
        assert result.transformed_value == "XYZ Team"  # Should return original
        assert "no_match_above_threshold" in result.applied_rules

    def test_process_batch(self):
        """Test batch processing of records."""
        records = [
            {
                "player_id": "1",
                "team_name": "la lakers",
                "position": "point guard",
                "points": "25",
                "rebounds": 10,
                "assists": 8,
            },
            {
                "player_id": "2",
                "team_name": "warriors",
                "position": "center",
                "points": "12",
                "rebounds": 15,
                "assists": 2,
            },
        ]

        cleaned_records, transformations = self.engine.process_batch(
            records, "player_stats"
        )

        assert len(cleaned_records) == 2
        assert len(transformations) > 0

        # Check transformations were applied
        assert cleaned_records[0]["team_name"] == "Los Angeles Lakers"
        assert cleaned_records[0]["position"] == "PG"
        assert cleaned_records[0]["points"] == 25.0

        assert cleaned_records[1]["team_name"] == "Golden State Warriors"
        assert cleaned_records[1]["position"] == "C"
        assert cleaned_records[1]["points"] == 12.0

    def test_get_transformation_summary(self):
        """Test transformation summary generation."""
        # Process some data to generate transformations
        records = [
            {"player_id": "1", "team_name": "lakers", "points": "25", "position": "pg"}
        ]

        self.engine.process_batch(records, "player_stats")
        summary = self.engine.get_transformation_summary()

        assert "total_transformations" in summary
        assert "successful_transformations" in summary
        assert "failed_transformations" in summary
        assert "success_rate" in summary
        assert "transformations_by_type" in summary
        assert summary["total_transformations"] > 0

    def test_clear_transformation_log(self):
        """Test clearing transformation log."""
        # Add some transformations
        result = self.engine.standardize_team_name("lakers")
        self.engine.transformation_log.append(result)

        assert len(self.engine.transformation_log) > 0

        self.engine.clear_transformation_log()
        assert len(self.engine.transformation_log) == 0


class TestTransformationResult:
    """Test cases for TransformationResult."""

    def test_transformation_result_creation(self):
        """Test creating TransformationResult."""
        result = TransformationResult(
            original_value="lakers",
            transformed_value="Los Angeles Lakers",
            transformation_type="team_name_standardization",
            success=True,
            applied_rules=["direct_mapping"],
        )

        assert result.original_value == "lakers"
        assert result.transformed_value == "Los Angeles Lakers"
        assert result.transformation_type == "team_name_standardization"
        assert result.success is True
        assert "direct_mapping" in result.applied_rules
        assert result.timestamp is not None

    def test_transformation_result_failure(self):
        """Test creating failed TransformationResult."""
        result = TransformationResult(
            original_value="invalid",
            transformed_value=None,
            transformation_type="numeric_cleaning",
            success=False,
            error_message="Invalid numeric value",
        )

        assert result.success is False
        assert result.error_message == "Invalid numeric value"
        assert result.transformed_value is None


class TestConfigurationLoading:
    """Test configuration loading and validation."""

    def test_default_config_loading(self):
        """Test that default configuration loads successfully."""
        engine = DataCleaningRulesEngine()

        assert engine.config is not None
        assert "version" in engine.config
        assert "team_name_mappings" in engine.config
        assert "position_mappings" in engine.config
        assert "null_handling" in engine.config

    def test_config_content_validation(self):
        """Test that configuration contains expected content."""
        engine = DataCleaningRulesEngine()

        # Check team mappings
        team_mappings = engine.config.get("team_name_mappings", {})
        assert "la lakers" in team_mappings
        assert team_mappings["la lakers"] == "Los Angeles Lakers"

        # Check position mappings
        position_mappings = engine.config.get("position_mappings", {})
        assert "point guard" in position_mappings
        assert position_mappings["point guard"] == "PG"

        # Check numeric validation
        numeric_validation = engine.config.get("numeric_validation", {})
        assert "points" in numeric_validation
        assert numeric_validation["points"]["min"] == 0
        assert numeric_validation["points"]["max"] == 100
