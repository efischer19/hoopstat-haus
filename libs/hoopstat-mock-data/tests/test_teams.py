"""Tests for NBA team generator."""

import pytest

from hoopstat_mock_data.generators.teams import TeamGenerator
from hoopstat_mock_data.models import Conference, Division, Team


class TestTeamGenerator:
    """Test cases for TeamGenerator."""

    def test_generate_teams_default_count(self):
        """Test generating the default 30 teams."""
        teams = TeamGenerator.generate_teams()

        assert len(teams) == 30
        assert all(isinstance(team, Team) for team in teams)

        # Check that all team IDs are unique
        team_ids = [team.id for team in teams]
        assert len(set(team_ids)) == 30

        # Check that abbreviations are unique
        abbreviations = [team.abbreviation for team in teams]
        assert len(set(abbreviations)) == 30

    def test_generate_teams_custom_count(self):
        """Test generating a custom number of teams."""
        teams = TeamGenerator.generate_teams(count=10)

        assert len(teams) == 10
        assert all(isinstance(team, Team) for team in teams)

    def test_generate_teams_max_count_exceeded(self):
        """Test that generating more than 30 teams raises an error."""
        with pytest.raises(ValueError, match="Cannot generate more than 30 NBA teams"):
            TeamGenerator.generate_teams(count=31)

    def test_team_attributes(self):
        """Test that teams have proper attributes."""
        teams = TeamGenerator.generate_teams(count=5)

        for team in teams:
            assert team.id > 0
            assert team.name
            assert team.city
            assert team.full_name == f"{team.city} {team.name}"
            assert len(team.abbreviation) == 3
            assert team.conference in [Conference.EASTERN, Conference.WESTERN]
            assert team.division in list(Division)

    def test_real_nba_teams(self):
        """Test that real NBA teams are generated."""
        teams = TeamGenerator.generate_teams(count=30)

        # Check for some well-known teams
        team_names = [team.name for team in teams]
        assert "Lakers" in team_names
        assert "Celtics" in team_names
        assert "Warriors" in team_names

        # Check for some well-known abbreviations
        abbreviations = [team.abbreviation for team in teams]
        assert "LAL" in abbreviations
        assert "BOS" in abbreviations
        assert "GSW" in abbreviations

    def test_get_team_by_id(self):
        """Test getting a team by ID."""
        team = TeamGenerator.get_team_by_id(1)
        assert isinstance(team, Team)
        assert team.id == 1

    def test_get_team_by_id_not_found(self):
        """Test getting a non-existent team by ID."""
        with pytest.raises(ValueError, match="Team with ID 999 not found"):
            TeamGenerator.get_team_by_id(999)

    def test_get_teams_by_conference(self):
        """Test getting teams by conference."""
        eastern_teams = TeamGenerator.get_teams_by_conference(Conference.EASTERN)
        western_teams = TeamGenerator.get_teams_by_conference(Conference.WESTERN)

        assert len(eastern_teams) == 15
        assert len(western_teams) == 15

        assert all(team.conference == Conference.EASTERN for team in eastern_teams)
        assert all(team.conference == Conference.WESTERN for team in western_teams)

    def test_get_teams_by_division(self):
        """Test getting teams by division."""
        atlantic_teams = TeamGenerator.get_teams_by_division(Division.ATLANTIC)

        assert len(atlantic_teams) == 5
        assert all(team.division == Division.ATLANTIC for team in atlantic_teams)
        assert all(team.conference == Conference.EASTERN for team in atlantic_teams)
