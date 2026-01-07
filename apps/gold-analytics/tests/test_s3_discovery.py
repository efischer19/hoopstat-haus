"""Tests for S3 discovery functions."""

from datetime import date

from app.s3_discovery import parse_s3_event_key


class TestParseS3EventKey:
    """Test cases for parse_s3_event_key function."""

    def test_parse_silver_ready_marker(self):
        """Test parsing silver-ready marker key."""
        s3_key = "metadata/2024-01-15/silver-ready.json"

        result = parse_s3_event_key(s3_key)

        assert result is not None
        assert result["file_type"] == "silver-ready-marker"
        assert result["date"] == date(2024, 1, 15)
        assert result["season"] == "2023-24"
        assert result["original_key"] == s3_key
        assert result["is_marker"] is True

    def test_parse_silver_ready_marker_different_date(self):
        """Test parsing silver-ready marker with different date."""
        s3_key = "metadata/2023-12-25/silver-ready.json"

        result = parse_s3_event_key(s3_key)

        assert result is not None
        assert result["file_type"] == "silver-ready-marker"
        assert result["date"] == date(2023, 12, 25)
        assert result["season"] == "2023-24"
        assert result["is_marker"] is True

    def test_parse_silver_data_file_without_season(self):
        """Test parsing Silver data file (current ADR-032 format)."""
        s3_key = "silver/player-stats/2024-01-15/players.json"

        result = parse_s3_event_key(s3_key)

        assert result is not None
        assert result["file_type"] == "player-stats"
        assert result["date"] == date(2024, 1, 15)
        assert result["season"] == "2023-24"
        assert result["original_key"] == s3_key
        assert result["is_marker"] is False

    def test_parse_silver_data_file_with_season(self):
        """Test parsing Silver data file with season (legacy format)."""
        s3_key = "silver/team_stats/season=2023-24/date=2024-01-15/teams.json"

        result = parse_s3_event_key(s3_key)

        assert result is not None
        assert result["file_type"] == "team_stats"
        assert result["date"] == date(2024, 1, 15)
        assert result["season"] == "2023-24"
        assert result["original_key"] == s3_key
        assert result["is_marker"] is False

    def test_parse_invalid_key(self):
        """Test parsing invalid S3 key."""
        s3_key = "invalid/key/structure"

        result = parse_s3_event_key(s3_key)

        assert result is None

    def test_parse_marker_invalid_date_format(self):
        """Test parsing marker with invalid date format."""
        s3_key = "metadata/invalid-date/silver-ready.json"

        result = parse_s3_event_key(s3_key)

        assert result is None

    def test_marker_takes_precedence(self):
        """Test that marker pattern is checked first."""
        # This ensures the marker pattern is prioritized
        s3_key = "metadata/2024-01-15/silver-ready.json"

        result = parse_s3_event_key(s3_key)

        assert result is not None
        assert result["is_marker"] is True
        assert result["file_type"] == "silver-ready-marker"
