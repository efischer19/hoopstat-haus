"""Tests for data validation functions."""

from hoopstat_data.validation import (
    validate_game_stats,
    validate_player_stats,
    validate_stat_ranges,
    validate_team_stats,
)


class TestValidatePlayerStats:
    """Test cases for player stats validation."""

    def test_valid_player_stats(self):
        """Test validation of valid player stats."""
        stats = {
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "steals": 2,
            "blocks": 1,
            "turnovers": 3,
        }

        assert validate_player_stats(stats) is True

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        stats = {
            "points": 25,
            "rebounds": 10,
            # Missing assists
        }

        assert validate_player_stats(stats) is False

    def test_negative_stats(self):
        """Test validation fails with negative stats."""
        stats = {"points": 25, "rebounds": -5, "assists": 5}  # Invalid negative value

        assert validate_player_stats(stats) is False

    def test_shooting_consistency(self):
        """Test shooting stats consistency validation."""
        # Valid shooting stats
        valid_stats = {
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "field_goals_made": 10,
            "field_goals_attempted": 15,
        }
        assert validate_player_stats(valid_stats) is True

        # Invalid shooting stats
        invalid_stats = {
            "points": 25,
            "rebounds": 10,
            "assists": 5,
            "field_goals_made": 15,
            "field_goals_attempted": 10,  # Less than made
        }
        assert validate_player_stats(invalid_stats) is False

    def test_unreasonable_values(self):
        """Test validation of unreasonably high values."""
        stats = {"points": 250, "rebounds": 10, "assists": 5}  # Unreasonably high

        assert validate_player_stats(stats) is False

    def test_empty_stats(self):
        """Test validation of empty stats dictionary."""
        assert validate_player_stats({}) is False


class TestValidateTeamStats:
    """Test cases for team stats validation."""

    def test_valid_team_stats(self):
        """Test validation of valid team stats."""
        stats = {
            "team_name": "Lakers",
            "points": 120,
            "field_goals_made": 45,
            "rebounds": 50,
            "assists": 25,
        }

        assert validate_team_stats(stats) is True

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        stats = {
            "points": 120
            # Missing team_name
        }

        assert validate_team_stats(stats) is False

    def test_invalid_team_name(self):
        """Test validation fails with invalid team name."""
        # Empty team name
        stats = {"team_name": "", "points": 120}
        assert validate_team_stats(stats) is False

        # None team name
        stats = {"team_name": None, "points": 120}
        assert validate_team_stats(stats) is False

        # Whitespace only team name
        stats = {"team_name": "   ", "points": 120}
        assert validate_team_stats(stats) is False

    def test_negative_team_stats(self):
        """Test validation fails with negative stats."""
        stats = {
            "team_name": "Lakers",
            "points": -120,  # Invalid negative value
            "field_goals_made": 45,
        }

        assert validate_team_stats(stats) is False


class TestValidateGameStats:
    """Test cases for game stats validation."""

    def test_valid_game_stats(self):
        """Test validation of valid game stats."""
        stats = {"game_id": "game_12345", "home_score": 110, "away_score": 105}

        assert validate_game_stats(stats) is True

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        stats = {
            "game_id": "game_12345",
            "home_score": 110,
            # Missing away_score
        }

        assert validate_game_stats(stats) is False

    def test_invalid_score_types(self):
        """Test validation fails with non-integer scores."""
        stats = {
            "game_id": "game_12345",
            "home_score": "110",  # String instead of int
            "away_score": 105,
        }

        assert validate_game_stats(stats) is False

    def test_negative_scores(self):
        """Test validation fails with negative scores."""
        stats = {
            "game_id": "game_12345",
            "home_score": -110,  # Invalid negative score
            "away_score": 105,
        }

        assert validate_game_stats(stats) is False

    def test_score_range_warnings(self):
        """Test validation handles unusual score ranges."""
        # Very high scores (should still pass but log warning)
        high_score_stats = {
            "game_id": "game_12345",
            "home_score": 250,
            "away_score": 240,
        }
        assert validate_game_stats(high_score_stats) is True

        # Very low scores (should still pass but log warning)
        low_score_stats = {"game_id": "game_12345", "home_score": 30, "away_score": 25}
        assert validate_game_stats(low_score_stats) is True


class TestValidateStatRanges:
    """Test cases for stat range validation."""

    def test_valid_stat_ranges(self):
        """Test validation of stats within expected ranges."""
        stats = {"points": 25, "rebounds": 10, "assists": 8}

        errors = validate_stat_ranges(stats)
        assert len(errors) == 0

    def test_out_of_range_stats(self):
        """Test detection of stats outside expected ranges."""
        stats = {"points": 150, "rebounds": -5, "assists": 8}  # Too high  # Too low

        errors = validate_stat_ranges(stats)
        assert len(errors) == 2
        assert "points value 150 is outside expected range" in errors[0]
        assert "rebounds value -5 is outside expected range" in errors[1]

    def test_custom_stat_ranges(self):
        """Test validation with custom stat ranges."""
        stats = {"points": 25, "rebounds": 10}

        custom_ranges = {"points": (0, 20), "rebounds": (0, 50)}  # Tighter range

        errors = validate_stat_ranges(stats, custom_ranges)
        assert len(errors) == 1
        assert "points value 25 is outside expected range (0, 20)" in errors[0]

    def test_none_values_ignored(self):
        """Test that None values are ignored in range validation."""
        stats = {"points": None, "rebounds": 10, "assists": None}

        errors = validate_stat_ranges(stats)
        assert len(errors) == 0

    def test_unknown_stats_ignored(self):
        """Test that unknown stats are ignored."""
        stats = {"points": 25, "unknown_stat": 999999}  # Should be ignored

        errors = validate_stat_ranges(stats)
        assert len(errors) == 0
