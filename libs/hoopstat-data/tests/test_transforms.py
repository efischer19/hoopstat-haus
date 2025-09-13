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


class TestPossessionsCalculation:
    """Test cases for possessions calculation."""

    def test_basic_possessions_calculation(self):
        """Test basic possessions calculation."""
        from hoopstat_data.transforms import calculate_possessions

        # Standard game stats
        possessions = calculate_possessions(85, 25, 12, 15)
        expected = 85 - 12 + 15 + 0.44 * 25  # FGA - ORB + TOV + 0.44 * FTA
        assert possessions == round(expected, 1)

    def test_possessions_with_zero_values(self):
        """Test possessions calculation with zero values."""
        from hoopstat_data.transforms import calculate_possessions

        assert calculate_possessions(0, 0, 0, 0) == 0.0
        assert calculate_possessions(10, 0, 0, 5) == 15.0

    def test_possessions_invalid_inputs(self):
        """Test possessions calculation with invalid inputs."""
        from hoopstat_data.transforms import calculate_possessions

        assert calculate_possessions(-1, 25, 12, 15) is None
        assert calculate_possessions(85, -1, 12, 15) is None
        assert calculate_possessions(85, 25, -1, 15) is None
        assert calculate_possessions(85, 25, 12, -1) is None


class TestOffensiveRating:
    """Test cases for Offensive Rating calculation."""

    def test_basic_offensive_rating(self):
        """Test basic Offensive Rating calculation."""
        from hoopstat_data.transforms import calculate_offensive_rating

        # 110 points on 95.5 possessions = 115.2 ORTG
        rating = calculate_offensive_rating(110, 95.5)
        expected = (110 / 95.5) * 100
        assert rating == round(expected, 1)

    def test_offensive_rating_edge_cases(self):
        """Test Offensive Rating with edge cases."""
        from hoopstat_data.transforms import calculate_offensive_rating

        assert calculate_offensive_rating(0, 95.5) == 0.0
        assert calculate_offensive_rating(110, 0) is None
        assert calculate_offensive_rating(-5, 95.5) is None


class TestDefensiveRating:
    """Test cases for Defensive Rating calculation."""

    def test_basic_defensive_rating(self):
        """Test basic Defensive Rating calculation."""
        from hoopstat_data.transforms import calculate_defensive_rating

        # 105 points allowed on 98.2 possessions = 107.0 DRTG
        rating = calculate_defensive_rating(105, 98.2)
        expected = (105 / 98.2) * 100
        assert rating == round(expected, 1)

    def test_defensive_rating_edge_cases(self):
        """Test Defensive Rating with edge cases."""
        from hoopstat_data.transforms import calculate_defensive_rating

        assert calculate_defensive_rating(0, 95.5) == 0.0
        assert calculate_defensive_rating(105, 0) is None
        assert calculate_defensive_rating(-5, 95.5) is None


class TestPaceCalculation:
    """Test cases for Pace calculation."""

    def test_basic_pace_calculation(self):
        """Test basic Pace calculation."""
        from hoopstat_data.transforms import calculate_pace

        # Standard regulation game
        pace = calculate_pace(95.5, 48.0)
        assert pace == 95.5  # Same value for 48 minutes

        # Overtime game
        pace = calculate_pace(105.0, 53.0)
        expected = (105.0 / 53.0) * 48
        assert pace == round(expected, 1)

    def test_pace_edge_cases(self):
        """Test Pace with edge cases."""
        from hoopstat_data.transforms import calculate_pace

        assert calculate_pace(0, 48.0) is None
        assert calculate_pace(95.5, 0) is None
        assert calculate_pace(-5, 48.0) is None


class TestEffectiveFieldGoalPercentage:
    """Test cases for Effective Field Goal Percentage calculation."""

    def test_basic_efg_calculation(self):
        """Test basic eFG% calculation."""
        from hoopstat_data.transforms import calculate_effective_field_goal_percentage

        # 42 FGM, 85 FGA, 12 3PM
        efg = calculate_effective_field_goal_percentage(42, 85, 12)
        expected = (42 + 0.5 * 12) / 85
        assert efg == round(expected, 3)

    def test_efg_no_threes(self):
        """Test eFG% with no three-pointers."""
        from hoopstat_data.transforms import calculate_effective_field_goal_percentage

        efg = calculate_effective_field_goal_percentage(20, 40, 0)
        assert efg == 0.5  # Same as regular FG%

    def test_efg_edge_cases(self):
        """Test eFG% with edge cases."""
        from hoopstat_data.transforms import calculate_effective_field_goal_percentage

        assert (
            calculate_effective_field_goal_percentage(42, 0, 12) is None
        )  # No attempts
        assert (
            calculate_effective_field_goal_percentage(-1, 85, 12) is None
        )  # Negative makes
        assert (
            calculate_effective_field_goal_percentage(90, 85, 12) is None
        )  # More makes than attempts


class TestTurnoverPercentage:
    """Test cases for Turnover Percentage calculation."""

    def test_basic_turnover_percentage(self):
        """Test basic TOV% calculation."""
        from hoopstat_data.transforms import calculate_turnover_percentage

        # 15 turnovers on 95.5 possessions
        tov_pct = calculate_turnover_percentage(15, 95.5)
        expected = (15 / 95.5) * 100
        assert tov_pct == round(expected, 1)

    def test_turnover_percentage_edge_cases(self):
        """Test TOV% with edge cases."""
        from hoopstat_data.transforms import calculate_turnover_percentage

        assert calculate_turnover_percentage(0, 95.5) == 0.0
        assert calculate_turnover_percentage(15, 0) is None
        assert calculate_turnover_percentage(-1, 95.5) is None


class TestOffensiveReboundPercentage:
    """Test cases for Offensive Rebound Percentage calculation."""

    def test_basic_orb_percentage(self):
        """Test basic ORB% calculation."""
        from hoopstat_data.transforms import calculate_offensive_rebound_percentage

        # 12 ORB, 85 FGA, 42 FGM (43 missed shots)
        orb_pct = calculate_offensive_rebound_percentage(12, 85, 42)
        missed_shots = 85 - 42
        expected = (12 / missed_shots) * 100
        assert orb_pct == round(expected, 1)

    def test_orb_percentage_edge_cases(self):
        """Test ORB% with edge cases."""
        from hoopstat_data.transforms import calculate_offensive_rebound_percentage

        # No missed shots (perfect shooting)
        assert calculate_offensive_rebound_percentage(12, 42, 42) is None
        assert calculate_offensive_rebound_percentage(-1, 85, 42) is None
        assert calculate_offensive_rebound_percentage(0, 85, 42) == 0.0


class TestFreeThrowRate:
    """Test cases for Free Throw Rate calculation."""

    def test_basic_ft_rate(self):
        """Test basic FT Rate calculation."""
        from hoopstat_data.transforms import calculate_free_throw_rate

        # 25 FTA, 85 FGA
        ft_rate = calculate_free_throw_rate(25, 85)
        expected = 25 / 85
        assert ft_rate == round(expected, 3)

    def test_ft_rate_edge_cases(self):
        """Test FT Rate with edge cases."""
        from hoopstat_data.transforms import calculate_free_throw_rate

        assert calculate_free_throw_rate(0, 85) == 0.0
        assert calculate_free_throw_rate(25, 0) is None
        assert calculate_free_throw_rate(-1, 85) is None


class TestTeamSeasonAggregator:
    """Test cases for TeamSeasonAggregator class."""

    def test_aggregator_initialization(self):
        """Test TeamSeasonAggregator initialization."""
        from hoopstat_data.transforms import TeamSeasonAggregator

        aggregator = TeamSeasonAggregator()
        assert aggregator.validation_mode == "strict"

        aggregator_lenient = TeamSeasonAggregator(validation_mode="lenient")
        assert aggregator_lenient.validation_mode == "lenient"

    def test_aggregate_season_stats_basic(self):
        """Test basic season stats aggregation for teams."""
        from hoopstat_data.transforms import TeamSeasonAggregator

        aggregator = TeamSeasonAggregator(validation_mode="lenient")

        team_games = [
            {
                "team_id": "1610612747",
                "team_name": "Los Angeles Lakers",
                "points": 110,
                "points_allowed": 105,
                "field_goals_made": 42,
                "field_goals_attempted": 85,
                "three_pointers_made": 12,
                "three_pointers_attempted": 35,
                "free_throws_made": 14,
                "free_throws_attempted": 18,
                "offensive_rebounds": 12,
                "defensive_rebounds": 32,
                "total_rebounds": 44,
                "assists": 25,
                "steals": 8,
                "blocks": 5,
                "turnovers": 15,
                "is_home": True,
                "win": True,
                "game_date": "2024-01-15",
            },
            {
                "team_id": "1610612747",
                "team_name": "Los Angeles Lakers",
                "points": 98,
                "points_allowed": 102,
                "field_goals_made": 38,
                "field_goals_attempted": 88,
                "three_pointers_made": 8,
                "three_pointers_attempted": 32,
                "free_throws_made": 14,
                "free_throws_attempted": 20,
                "offensive_rebounds": 10,
                "defensive_rebounds": 35,
                "total_rebounds": 45,
                "assists": 22,
                "steals": 6,
                "blocks": 3,
                "turnovers": 18,
                "is_home": False,
                "win": False,
                "game_date": "2024-01-18",
            },
        ]

        season_stats = aggregator.aggregate_season_stats(team_games, "2023-24")

        # Basic checks
        assert season_stats["team_id"] == "1610612747"
        assert season_stats["team_name"] == "Los Angeles Lakers"
        assert season_stats["season"] == "2023-24"
        assert season_stats["total_games"] == 2

        # Check totals
        assert season_stats["total_points"] == 208
        assert season_stats["total_points_allowed"] == 207

        # Check averages
        assert season_stats["points_per_game"] == 104.0
        assert season_stats["points_allowed_per_game"] == 103.5

        # Check advanced metrics exist
        assert "offensive_rating" in season_stats
        assert "defensive_rating" in season_stats
        assert "net_rating" in season_stats
        assert "pace" in season_stats

        # Check Four Factors
        assert "effective_field_goal_percentage" in season_stats
        assert "turnover_percentage" in season_stats
        assert "offensive_rebound_percentage" in season_stats
        assert "free_throw_rate" in season_stats

        # Check splits
        assert "home_away_splits" in season_stats
        assert "monthly_splits" in season_stats

    def test_aggregate_season_stats_empty_data(self):
        """Test season stats aggregation with empty data."""
        from hoopstat_data.transforms import TeamSeasonAggregator

        aggregator = TeamSeasonAggregator()
        season_stats = aggregator.aggregate_season_stats([], "2023-24")

        assert season_stats["total_games"] == 0
        assert "error" in season_stats

    def test_home_away_splits(self):
        """Test home/away splits calculation."""
        from hoopstat_data.transforms import TeamSeasonAggregator

        aggregator = TeamSeasonAggregator(validation_mode="lenient")

        team_games = [
            {
                "team_id": "1610612747",
                "points": 110,
                "points_allowed": 105,
                "field_goals_attempted": 85,
                "is_home": True,
                "win": True,
            },
            {
                "team_id": "1610612747",
                "points": 98,
                "points_allowed": 102,
                "field_goals_attempted": 88,
                "is_home": False,
                "win": False,
            },
        ]

        season_stats = aggregator.aggregate_season_stats(team_games, "2023-24")

        home_splits = season_stats["home_away_splits"]["home"]
        away_splits = season_stats["home_away_splits"]["away"]

        assert home_splits["games"] == 1
        assert home_splits["wins"] == 1
        assert home_splits["win_percentage"] == 1.0
        assert home_splits["points_per_game"] == 110.0

        assert away_splits["games"] == 1
        assert away_splits["wins"] == 0
        assert away_splits["win_percentage"] == 0.0
        assert away_splits["points_per_game"] == 98.0
