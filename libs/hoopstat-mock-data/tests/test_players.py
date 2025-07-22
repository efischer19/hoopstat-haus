"""Tests for NBA player generator."""

from hoopstat_mock_data.generators.players import PlayerGenerator
from hoopstat_mock_data.generators.teams import TeamGenerator
from hoopstat_mock_data.models import Player, Position


class TestPlayerGenerator:
    """Test cases for PlayerGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PlayerGenerator(seed=42)
        self.teams = TeamGenerator.generate_teams(count=2)

    def test_generate_players_default(self):
        """Test generating players with default settings."""
        players = self.generator.generate_players(self.teams)

        expected_count = len(self.teams) * 15  # 15 players per team
        assert len(players) == expected_count
        assert all(isinstance(player, Player) for player in players)

    def test_generate_players_custom_count(self):
        """Test generating players with custom count per team."""
        players = self.generator.generate_players(self.teams, players_per_team=10)

        expected_count = len(self.teams) * 10
        assert len(players) == expected_count

    def test_player_attributes(self):
        """Test that players have proper attributes."""
        players = self.generator.generate_players(self.teams, players_per_team=5)

        for player in players:
            assert player.id > 0
            assert player.first_name
            assert player.last_name
            assert player.full_name == f"{player.first_name} {player.last_name}"
            assert player.team_id in [team.id for team in self.teams]
            assert player.position in list(Position)
            assert 0 <= player.jersey_number <= 99
            assert 60 <= player.height_inches <= 96
            assert 150 <= player.weight_pounds <= 350
            assert 18 <= player.age <= 50
            assert 0 <= player.years_experience <= 25
            assert player.years_experience <= player.age - 18

    def test_jersey_number_uniqueness(self):
        """Test that jersey numbers are unique within teams."""
        players = self.generator.generate_players(self.teams, players_per_team=15)

        # Group players by team
        team_players = {}
        for player in players:
            if player.team_id not in team_players:
                team_players[player.team_id] = []
            team_players[player.team_id].append(player)

        # Check jersey number uniqueness within each team
        for team_id, team_player_list in team_players.items():
            jersey_numbers = [p.jersey_number for p in team_player_list]
            assert len(set(jersey_numbers)) == len(jersey_numbers), (
                f"Duplicate jersey numbers in team {team_id}"
            )

    def test_position_distribution(self):
        """Test that positions are distributed reasonably."""
        players = self.generator.generate_players(self.teams, players_per_team=15)

        positions = [player.position for player in players]
        position_counts = {pos: positions.count(pos) for pos in Position}

        # Should have at least one player in each position
        for position in Position:
            assert position_counts[position] > 0

    def test_height_weight_correlation(self):
        """Test that height and weight are correlated by position."""
        players = self.generator.generate_players(self.teams, players_per_team=15)

        # Group by position
        position_players = {pos: [] for pos in Position}
        for player in players:
            position_players[player.position].append(player)

        # Centers should generally be taller than point guards
        if position_players[Position.CENTER] and position_players[Position.POINT_GUARD]:
            avg_center_height = sum(
                p.height_inches for p in position_players[Position.CENTER]
            ) / len(position_players[Position.CENTER])
            avg_pg_height = sum(
                p.height_inches for p in position_players[Position.POINT_GUARD]
            ) / len(position_players[Position.POINT_GUARD])

            assert avg_center_height > avg_pg_height

    def test_generate_single_player(self):
        """Test generating a single player."""
        player = self.generator.generate_single_player(
            team_id=1, position=Position.POINT_GUARD, jersey_number=23
        )

        assert isinstance(player, Player)
        assert player.team_id == 1
        assert player.position == Position.POINT_GUARD
        assert player.jersey_number == 23

    def test_generate_single_player_random(self):
        """Test generating a single player with random attributes."""
        player = self.generator.generate_single_player(team_id=1)

        assert isinstance(player, Player)
        assert player.team_id == 1
        assert player.position in list(Position)
        assert 1 <= player.jersey_number <= 99

    def test_reproducible_generation(self):
        """Test that generation is reproducible with the same seed."""
        generator1 = PlayerGenerator(seed=42)
        generator2 = PlayerGenerator(seed=42)

        players1 = generator1.generate_players(self.teams, players_per_team=5)
        players2 = generator2.generate_players(self.teams, players_per_team=5)

        assert len(players1) == len(players2)

        for p1, p2 in zip(players1, players2, strict=False):
            assert p1.first_name == p2.first_name
            assert p1.last_name == p2.last_name
            assert p1.position == p2.position
            assert p1.height_inches == p2.height_inches
            assert p1.weight_pounds == p2.weight_pounds
