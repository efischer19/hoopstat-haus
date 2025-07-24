"""Tests for data transformation utilities."""

from hoopstat_data.transforms import (
    calculate_efficiency_rating,
    calculate_shooting_percentage,
    clean_and_transform_record,
    clean_batch,
    convert_minutes_to_decimal,
    normalize_stat_per_game,
    normalize_team_name,
    standardize_position,
    validate_and_standardize_season,
)


class TestNormalizeTeamName:
    """Test cases for team name normalization."""

    def test_basic_normalization(self):
        """Test basic team name normalization."""
        # With rules engine (default) - returns full official names
        assert normalize_team_name("lakers") == "Los Angeles Lakers"
        assert normalize_team_name("LAKERS") == "Los Angeles Lakers"
        assert normalize_team_name("  lakers  ") == "Los Angeles Lakers"

        # Without rules engine - returns simple form
        assert normalize_team_name("lakers", use_rules_engine=False) == "Lakers"

    def test_common_team_mappings(self):
        """Test normalization of common team name variations."""
        # With rules engine
        assert normalize_team_name("LA Lakers") == "Los Angeles Lakers"
        assert normalize_team_name("Los Angeles Lakers") == "Los Angeles Lakers"
        assert normalize_team_name("L.A. Lakers") == "Los Angeles Lakers"
        assert normalize_team_name("Golden State Warriors") == "Golden State Warriors"
        assert normalize_team_name("Boston Celtics") == "Boston Celtics"

        # Test fallback without rules engine
        assert normalize_team_name("LA Lakers", use_rules_engine=False) == "Lakers"

    def test_multi_word_teams(self):
        """Test normalization of multi-word team names."""
        # With rules engine - returns full official names
        assert normalize_team_name("trail blazers") == "Portland Trail Blazers"
        assert normalize_team_name("new york knicks") == "New York Knicks"

        # Without rules engine - uses title case
        assert (
            normalize_team_name("trail blazers", use_rules_engine=False)
            == "Trail Blazers"
        )

    def test_edge_cases(self):
        """Test edge cases for team name normalization."""
        # With rules engine, empty/None should fall back to original logic
        assert normalize_team_name("") == ""
        assert normalize_team_name(None) == ""  # Should fall back and return ""
        assert normalize_team_name("   ") == ""

        # Test fallback behavior
        assert normalize_team_name("", use_rules_engine=False) == ""
        assert normalize_team_name(None, use_rules_engine=False) == ""
        assert (
            normalize_team_name(123, use_rules_engine=False) == ""
        )  # Non-string input


class TestCalculateEfficiencyRating:
    """Test cases for efficiency rating calculation."""

    def test_basic_efficiency_calculation(self):
        """Test basic efficiency rating calculation."""
        stats = {
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
            "minutes_played": 35,
        }

        # (25 + 10 + 5 + 2 + 1 - 3) / 35 = 40 / 35 ≈ 1.14
        expected = 1.14
        assert calculate_efficiency_rating(stats) == expected

    def test_missing_stats_default_to_zero(self):
        """Test that missing stats default to zero."""
        stats = {"points": 20, "minutes_played": 20}

        # (20 + 0 + 0 + 0 + 0 - 0) / 20 = 1.0
        assert calculate_efficiency_rating(stats) == 1.0

    def test_zero_minutes_handling(self):
        """Test handling of zero or missing minutes."""
        stats = {"points": 25, "rebounds": 10, "minutes_played": 0}

        assert calculate_efficiency_rating(stats) == 0.0

        # Test missing minutes_played
        stats_no_minutes = {"points": 25, "rebounds": 10}

        # Should use default 1 minute to avoid division by zero
        assert calculate_efficiency_rating(stats_no_minutes) == 35.0

    def test_negative_efficiency(self):
        """Test calculation with more turnovers than positive stats."""
        stats = {
            "points": 5,
            "rebounds": 2,
            "assists": 1,
            "turnovers": 15,
            "minutes_played": 30,
        }

        # (5 + 2 + 1 - 15) / 30 = -7 / 30 ≈ -0.23
        assert calculate_efficiency_rating(stats) == -0.23

    def test_exception_handling(self):
        """Test exception handling in efficiency calculation."""
        # Invalid data should return 0.0
        invalid_stats = {"invalid": "data"}
        assert calculate_efficiency_rating(invalid_stats) == 0.0


class TestStandardizePosition:
    """Test cases for position standardization."""

    def test_standard_positions(self):
        """Test standardization of common position names."""
        assert standardize_position("Point Guard") == "PG"
        assert standardize_position("Shooting Guard") == "SG"
        assert standardize_position("Small Forward") == "SF"
        assert standardize_position("Power Forward") == "PF"
        assert standardize_position("Center") == "C"

    def test_case_insensitive(self):
        """Test case-insensitive position standardization."""
        assert standardize_position("point guard") == "PG"
        assert standardize_position("SHOOTING GUARD") == "SG"
        assert standardize_position("center") == "C"

    def test_abbreviations(self):
        """Test handling of position abbreviations."""
        assert standardize_position("PG") == "PG"
        assert standardize_position("sg") == "SG"
        assert standardize_position("C") == "C"

    def test_generic_positions(self):
        """Test handling of generic position names."""
        assert standardize_position("Guard") == "G"
        assert standardize_position("Forward") == "F"

    def test_partial_matches(self):
        """Test partial string matching for positions."""
        assert standardize_position("Point Guard / Forward") == "PG"
        assert standardize_position("Shooting Guard Position") == "SG"

    def test_edge_cases(self):
        """Test edge cases for position standardization."""
        assert standardize_position("") == "UNKNOWN"
        assert standardize_position(None) == "UNKNOWN"
        assert standardize_position("Unknown Position") == "UNKNOWN"
        assert standardize_position(123) == "UNKNOWN"


class TestCalculateShootingPercentage:
    """Test cases for shooting percentage calculation."""

    def test_valid_shooting_percentage(self):
        """Test calculation of valid shooting percentage."""
        assert calculate_shooting_percentage(8, 15) == 0.533
        assert calculate_shooting_percentage(10, 10) == 1.0
        assert calculate_shooting_percentage(0, 5) == 0.0

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        assert calculate_shooting_percentage(0, 0) is None  # No attempts
        assert calculate_shooting_percentage(-1, 5) is None  # Negative made
        assert calculate_shooting_percentage(6, 5) is None  # More made than attempted
        assert calculate_shooting_percentage(5, -1) is None  # Negative attempted


class TestConvertMinutesToDecimal:
    """Test cases for minutes conversion."""

    def test_valid_minute_conversion(self):
        """Test conversion of valid time strings."""
        assert convert_minutes_to_decimal("35:30") == 35.5
        assert convert_minutes_to_decimal("12:45") == 12.75
        assert convert_minutes_to_decimal("0:30") == 0.5
        assert convert_minutes_to_decimal("48:00") == 48.0

    def test_decimal_format_input(self):
        """Test handling of already decimal format."""
        assert convert_minutes_to_decimal("35.5") == 35.5
        assert convert_minutes_to_decimal("12.75") == 12.75

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        assert convert_minutes_to_decimal("") is None
        assert convert_minutes_to_decimal(None) is None
        assert convert_minutes_to_decimal("invalid") is None
        assert convert_minutes_to_decimal("35:") is None
        assert convert_minutes_to_decimal("35:75") is None  # Invalid seconds
        assert convert_minutes_to_decimal(123) is None  # Non-string input


class TestNormalizeStatPerGame:
    """Test cases for per-game stat normalization."""

    def test_valid_normalization(self):
        """Test valid per-game stat normalization."""
        assert normalize_stat_per_game(250, 10) == 25.0
        assert normalize_stat_per_game(100.5, 5) == 20.1
        assert normalize_stat_per_game(0, 10) == 0.0

    def test_invalid_games_played(self):
        """Test handling of invalid games played."""
        assert normalize_stat_per_game(250, 0) is None
        assert normalize_stat_per_game(250, -5) is None

    def test_rounding(self):
        """Test proper rounding of results."""
        assert normalize_stat_per_game(100, 3) == 33.3
        assert normalize_stat_per_game(200, 7) == 28.6


class TestCleanAndTransformRecord:
    """Test cases for clean_and_transform_record function."""

    def test_basic_record_cleaning(self):
        """Test basic record cleaning and transformation."""
        record = {
            "player_id": "123",
            "team_name": "lakers",
            "position": "point guard",
            "points": "25",
            "rebounds": 10,
            "assists": 5,
        }

        cleaned = clean_and_transform_record(record, "player_stats")

        assert cleaned["player_id"] == "123"
        assert cleaned["team_name"] == "Los Angeles Lakers"
        assert cleaned["position"] == "PG"
        assert cleaned["points"] == 25
        assert cleaned["rebounds"] == 10
        assert cleaned["assists"] == 5

    def test_fallback_cleaning(self):
        """Test fallback cleaning without rules engine."""
        record = {"team_name": "warriors", "position": "center", "points": "30"}

        cleaned = clean_and_transform_record(
            record, "player_stats", use_rules_engine=False
        )

        # Should still apply basic transformations
        assert "Warriors" in cleaned["team_name"]
        assert cleaned["position"] == "C"
        assert cleaned["points"] == 30


class TestCleanBatch:
    """Test cases for clean_batch function."""

    def test_batch_cleaning(self):
        """Test batch cleaning of multiple records."""
        records = [
            {"team_name": "lakers", "points": "25"},
            {"team_name": "warriors", "points": "30"},
            {"team_name": "celtics", "points": "28"},
        ]

        cleaned_records = clean_batch(records, "player_stats")

        assert len(cleaned_records) == 3
        assert cleaned_records[0]["team_name"] == "Los Angeles Lakers"
        assert cleaned_records[1]["team_name"] == "Golden State Warriors"
        assert cleaned_records[2]["team_name"] == "Boston Celtics"

        # Check numeric conversion
        assert all(
            isinstance(record["points"], int | float) for record in cleaned_records
        )

    def test_batch_cleaning_with_batch_size(self):
        """Test batch cleaning with specific batch size."""
        records = [{"team_name": f"team_{i}", "points": str(i * 10)} for i in range(5)]

        cleaned_records = clean_batch(records, "player_stats", batch_size=2)

        assert len(cleaned_records) == 5
        # All should be processed regardless of batch size


class TestValidateAndStandardizeSeason:
    """Test cases for season validation and standardization."""

    def test_full_year_format(self):
        """Test standardization of full year format."""
        assert validate_and_standardize_season("2023-2024") == "2023-24"
        assert validate_and_standardize_season("2022-2023") == "2022-23"

    def test_short_year_format(self):
        """Test standardization of short year format."""
        assert validate_and_standardize_season("23-24") == "2023-24"
        assert validate_and_standardize_season("22-23") == "2022-23"

    def test_already_correct_format(self):
        """Test seasons already in correct format."""
        assert validate_and_standardize_season("2023-24") == "2023-24"
        assert validate_and_standardize_season("2022-23") == "2022-23"

    def test_invalid_season_formats(self):
        """Test invalid season formats."""
        assert validate_and_standardize_season("2023") is None
        assert validate_and_standardize_season("invalid") is None
        assert validate_and_standardize_season("") is None
        assert validate_and_standardize_season(None) is None

    def test_invalid_year_sequences(self):
        """Test invalid year sequences."""
        # Years not consecutive
        assert validate_and_standardize_season("2023-2025") is None
        assert validate_and_standardize_season("23-25") is None

    def test_whitespace_handling(self):
        """Test handling of whitespace in season strings."""
        assert validate_and_standardize_season("  2023-24  ") == "2023-24"
        assert validate_and_standardize_season("  23-24  ") == "2023-24"
