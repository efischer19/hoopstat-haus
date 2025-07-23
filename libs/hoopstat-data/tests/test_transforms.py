"""Tests for data transformation utilities."""

from hoopstat_data.transforms import (
    calculate_efficiency_rating,
    calculate_shooting_percentage,
    convert_minutes_to_decimal,
    normalize_stat_per_game,
    normalize_team_name,
    standardize_position,
)


class TestNormalizeTeamName:
    """Test cases for team name normalization."""

    def test_basic_normalization(self):
        """Test basic team name normalization."""
        assert normalize_team_name("lakers") == "Lakers"
        assert normalize_team_name("LAKERS") == "Lakers"
        assert normalize_team_name("  lakers  ") == "Lakers"

    def test_common_team_mappings(self):
        """Test normalization of common team name variations."""
        assert normalize_team_name("LA Lakers") == "Lakers"
        assert normalize_team_name("Los Angeles Lakers") == "Lakers"
        assert normalize_team_name("L.A. Lakers") == "Lakers"
        assert normalize_team_name("Golden State Warriors") == "Warriors"
        assert normalize_team_name("Boston Celtics") == "Celtics"

    def test_multi_word_teams(self):
        """Test normalization of multi-word team names."""
        assert normalize_team_name("trail blazers") == "Trail Blazers"
        assert normalize_team_name("new york knicks") == "New York Knicks"

    def test_edge_cases(self):
        """Test edge cases for team name normalization."""
        assert normalize_team_name("") == ""
        assert normalize_team_name(None) == ""
        assert normalize_team_name("   ") == ""
        assert normalize_team_name(123) == ""  # Non-string input


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
