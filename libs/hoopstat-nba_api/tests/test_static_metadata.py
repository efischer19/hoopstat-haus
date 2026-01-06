"""
Tests for static metadata JSON files.
"""

import json
from pathlib import Path

import pytest


def get_static_dir():
    """Get the path to the static directory."""
    return Path(__file__).parent.parent / "hoopstat_nba_api" / "static"


class TestTeamsMetadata:
    """Tests for teams_v1.json metadata file."""

    @pytest.fixture
    def teams_data(self):
        """Load teams metadata."""
        teams_file = get_static_dir() / "teams_v1.json"
        with open(teams_file) as f:
            return json.load(f)

    def test_teams_file_exists(self):
        """Test that teams_v1.json exists."""
        teams_file = get_static_dir() / "teams_v1.json"
        assert teams_file.exists(), "teams_v1.json should exist"

    def test_teams_has_schema_version(self, teams_data):
        """Test that teams metadata has schema version."""
        assert "schema_version" in teams_data
        assert teams_data["schema_version"] == "v1"

    def test_teams_has_teams_array(self, teams_data):
        """Test that teams metadata has teams array."""
        assert "teams" in teams_data
        assert isinstance(teams_data["teams"], list)
        assert len(teams_data["teams"]) == 30, "Should have 30 NBA teams"

    def test_team_has_required_fields(self, teams_data):
        """Test that each team has required fields."""
        required_fields = {"id", "name", "abbreviation", "city", "conference"}

        for team in teams_data["teams"]:
            assert all(field in team for field in required_fields), (
                f"Team missing required fields: {team}"
            )

    def test_team_ids_are_unique(self, teams_data):
        """Test that team IDs are unique."""
        team_ids = [team["id"] for team in teams_data["teams"]]
        assert len(team_ids) == len(set(team_ids)), "Team IDs should be unique"

    def test_team_abbreviations_are_unique(self, teams_data):
        """Test that team abbreviations are unique."""
        abbrevs = [team["abbreviation"] for team in teams_data["teams"]]
        assert len(abbrevs) == len(set(abbrevs)), "Team abbreviations should be unique"

    def test_teams_sorted_by_name(self, teams_data):
        """Test that teams are sorted by name."""
        team_names = [team["name"] for team in teams_data["teams"]]
        assert team_names == sorted(team_names), (
            "Teams should be sorted alphabetically by name"
        )

    def test_team_conferences_valid(self, teams_data):
        """Test that team conferences are valid values."""
        valid_conferences = {"Eastern", "Western"}
        for team in teams_data["teams"]:
            assert team["conference"] in valid_conferences, (
                f"Invalid conference for team: {team}"
            )


class TestPlayersMetadata:
    """Tests for players_v1.json metadata file."""

    @pytest.fixture
    def players_data(self):
        """Load players metadata."""
        players_file = get_static_dir() / "players_v1.json"
        with open(players_file) as f:
            return json.load(f)

    def test_players_file_exists(self):
        """Test that players_v1.json exists."""
        players_file = get_static_dir() / "players_v1.json"
        assert players_file.exists(), "players_v1.json should exist"

    def test_players_has_schema_version(self, players_data):
        """Test that players metadata has schema version."""
        assert "schema_version" in players_data
        assert players_data["schema_version"] == "v1"

    def test_players_has_players_array(self, players_data):
        """Test that players metadata has players array."""
        assert "players" in players_data
        assert isinstance(players_data["players"], list)
        assert len(players_data["players"]) > 0, "Should have active players"

    def test_player_has_required_fields(self, players_data):
        """Test that each player has required fields."""
        required_fields = {"id", "name", "active"}

        for player in players_data["players"]:
            assert all(field in player for field in required_fields), (
                f"Player missing required fields: {player}"
            )

    def test_all_players_are_active(self, players_data):
        """Test that all players in the file are active."""
        for player in players_data["players"]:
            assert player["active"] is True, f"Player should be active: {player}"

    def test_player_ids_are_unique(self, players_data):
        """Test that player IDs are unique."""
        player_ids = [player["id"] for player in players_data["players"]]
        assert len(player_ids) == len(set(player_ids)), "Player IDs should be unique"

    def test_players_sorted_by_name(self, players_data):
        """Test that players are sorted by name."""
        player_names = [player["name"] for player in players_data["players"]]
        assert player_names == sorted(player_names), (
            "Players should be sorted alphabetically by name"
        )

    def test_file_size_reasonable(self):
        """Test that the players file is reasonably sized."""
        players_file = get_static_dir() / "players_v1.json"
        file_size = players_file.stat().st_size
        # Should be less than 100KB for active players only
        assert file_size < 100 * 1024, f"Players file too large: {file_size} bytes"
