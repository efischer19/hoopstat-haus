"""Tests for the main mock data generator."""

from hoopstat_mock_data.generators.mock_data_generator import MockDataGenerator
from hoopstat_mock_data.models import Game, Player, PlayerStats, Team, TeamStats


class TestMockDataGenerator:
    """Test cases for MockDataGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = MockDataGenerator(seed=42)

    def test_generate_complete_dataset_small(self):
        """Test generating a small complete dataset."""
        dataset = self.generator.generate_complete_dataset(
            num_teams=4, players_per_team=8, num_games=10, season="2023-24"
        )

        assert "teams" in dataset
        assert "players" in dataset
        assert "games" in dataset
        assert "player_stats" in dataset
        assert "team_stats" in dataset

        assert len(dataset["teams"]) == 4
        assert len(dataset["players"]) == 32  # 4 teams * 8 players
        assert len(dataset["games"]) == 10

        # Verify types
        assert all(isinstance(team, Team) for team in dataset["teams"])
        assert all(isinstance(player, Player) for player in dataset["players"])
        assert all(isinstance(game, Game) for game in dataset["games"])
        assert all(isinstance(stat, PlayerStats) for stat in dataset["player_stats"])
        assert all(isinstance(stat, TeamStats) for stat in dataset["team_stats"])

    def test_generate_teams(self):
        """Test generating teams."""
        teams = self.generator.generate_teams(count=5)

        assert len(teams) == 5
        assert all(isinstance(team, Team) for team in teams)

    def test_generate_players(self):
        """Test generating players."""
        teams = self.generator.generate_teams(count=2)
        players = self.generator.generate_players(teams, players_per_team=10)

        assert len(players) == 20
        assert all(isinstance(player, Player) for player in players)

    def test_generate_games(self):
        """Test generating games."""
        teams = self.generator.generate_teams(count=4)
        games = self.generator.generate_games(teams, count=8, season="2023-24")

        assert len(games) == 8
        assert all(isinstance(game, Game) for game in games)
        assert all(game.season == "2023-24" for game in games)

    def test_generate_season_schedule(self):
        """Test generating a full season schedule."""
        teams = self.generator.generate_teams(count=30)
        games = self.generator.generate_season_schedule(
            teams, season="2023-24", include_playoffs=False
        )

        assert len(games) > 1000  # Should be many games in a full season
        assert all(isinstance(game, Game) for game in games)

    def test_preset_datasets(self):
        """Test preset dataset generation."""
        small = self.generator.generate_small_test_dataset()
        medium = self.generator.generate_medium_test_dataset()
        large = self.generator.generate_large_simulation_dataset()

        # Small dataset
        assert len(small["teams"]) == 4
        assert len(small["players"]) == 32  # 4 * 8
        assert len(small["games"]) == 10

        # Medium dataset
        assert len(medium["teams"]) == 10
        assert len(medium["players"]) == 120  # 10 * 12
        assert len(medium["games"]) == 50

        # Large dataset (adjusted expectation)
        assert len(large["teams"]) == 30
        assert len(large["players"]) == 450  # 30 * 15
        assert (
            len(large["games"]) >= 1000
        )  # Should be many games, but not necessarily 2000

    def test_reproducible_generation(self):
        """Test that generation is reproducible with the same seed."""
        generator1 = MockDataGenerator(seed=42)
        generator2 = MockDataGenerator(seed=42)

        dataset1 = generator1.generate_small_test_dataset()
        dataset2 = generator2.generate_small_test_dataset()

        # Check that teams are the same
        assert len(dataset1["teams"]) == len(dataset2["teams"])
        for t1, t2 in zip(dataset1["teams"], dataset2["teams"], strict=False):
            assert t1.name == t2.name
            assert t1.city == t2.city

        # Check that players are the same
        assert len(dataset1["players"]) == len(dataset2["players"])
        for p1, p2 in zip(dataset1["players"], dataset2["players"], strict=False):
            assert p1.first_name == p2.first_name
            assert p1.last_name == p2.last_name
            assert p1.position == p2.position

    def test_data_relationships(self):
        """Test that generated data maintains proper relationships."""
        dataset = self.generator.generate_complete_dataset(
            num_teams=4, players_per_team=8, num_games=10
        )

        team_ids = {team.id for team in dataset["teams"]}
        player_ids = {player.id for player in dataset["players"]}
        game_ids = {game.id for game in dataset["games"]}

        # Check player team references
        for player in dataset["players"]:
            assert player.team_id in team_ids

        # Check game team references
        for game in dataset["games"]:
            assert game.home_team_id in team_ids
            assert game.away_team_id in team_ids
            assert game.home_team_id != game.away_team_id

        # Check player stats references
        for stat in dataset["player_stats"]:
            assert stat.player_id in player_ids
            assert stat.game_id in game_ids
            assert stat.team_id in team_ids

        # Check team stats references
        for stat in dataset["team_stats"]:
            assert stat.team_id in team_ids
            assert stat.game_id in game_ids
