"""Main mock data generator that orchestrates all NBA data generation."""

from ..models import Game, Player, PlayerStats, Team, TeamStats
from .games import GameGenerator
from .players import PlayerGenerator
from .statistics import StatisticsGenerator
from .teams import TeamGenerator


class MockDataGenerator:
    """Main class for generating comprehensive NBA mock data."""

    def __init__(self, seed: int = None):
        """
        Initialize the mock data generator.

        Args:
            seed: Random seed for reproducible generation
        """
        self.seed = seed
        self.team_generator = TeamGenerator()
        self.player_generator = PlayerGenerator(seed=seed)
        self.game_generator = GameGenerator(seed=seed)
        self.stats_generator = StatisticsGenerator(seed=seed)

    def generate_complete_dataset(
        self,
        num_teams: int = 30,
        players_per_team: int = 15,
        num_games: int = 100,
        season: str = "2023-24",
        include_playoffs: bool = False,
    ) -> dict[str, list]:
        """
        Generate a complete NBA dataset with teams, players, games, and statistics.

        Args:
            num_teams: Number of teams to generate (max 30)
            players_per_team: Number of players per team
            num_games: Number of games to generate
            season: Season string (e.g., "2023-24")
            include_playoffs: Whether to include playoff games

        Returns:
            Dictionary containing all generated data
        """
        # Generate teams
        teams = self.team_generator.generate_teams(count=num_teams)

        # Generate players
        players = self.player_generator.generate_players(
            teams=teams, players_per_team=players_per_team
        )

        # Generate games
        if num_games > 1000 and num_teams == 30:
            # Generate full season schedule
            games = self.game_generator.generate_season_schedule(
                teams=teams, season=season, include_playoffs=include_playoffs
            )
        else:
            # Generate random games
            games = self.game_generator.generate_games(
                teams=teams, count=num_games, season=season
            )

        # Generate player statistics
        player_stats = self.stats_generator.generate_player_stats(
            players=players, games=games
        )

        # Generate team statistics
        team_stats = self.stats_generator.generate_team_stats(player_stats)

        return {
            "teams": teams,
            "players": players,
            "games": games,
            "player_stats": player_stats,
            "team_stats": team_stats,
        }

    def generate_teams(self, count: int = 30) -> list[Team]:
        """Generate NBA teams."""
        return self.team_generator.generate_teams(count=count)

    def generate_players(
        self, teams: list[Team], players_per_team: int = 15
    ) -> list[Player]:
        """Generate players for given teams."""
        return self.player_generator.generate_players(
            teams=teams, players_per_team=players_per_team
        )

    def generate_games(
        self, teams: list[Team], count: int, season: str = "2023-24"
    ) -> list[Game]:
        """Generate random games."""
        return self.game_generator.generate_games(
            teams=teams, count=count, season=season
        )

    def generate_season_schedule(
        self, teams: list[Team], season: str = "2023-24", include_playoffs: bool = True
    ) -> list[Game]:
        """Generate a complete season schedule."""
        return self.game_generator.generate_season_schedule(
            teams=teams, season=season, include_playoffs=include_playoffs
        )

    def generate_player_stats(
        self, players: list[Player], games: list[Game]
    ) -> list[PlayerStats]:
        """Generate player statistics for games."""
        return self.stats_generator.generate_player_stats(players=players, games=games)

    def generate_team_stats(self, player_stats: list[PlayerStats]) -> list[TeamStats]:
        """Generate team statistics from player statistics."""
        return self.stats_generator.generate_team_stats(player_stats)

    def generate_small_test_dataset(self) -> dict[str, list]:
        """Generate a small dataset suitable for unit tests."""
        return self.generate_complete_dataset(
            num_teams=4,
            players_per_team=8,
            num_games=10,
            season="2023-24",
            include_playoffs=False,
        )

    def generate_medium_test_dataset(self) -> dict[str, list]:
        """Generate a medium dataset suitable for integration tests."""
        return self.generate_complete_dataset(
            num_teams=10,
            players_per_team=12,
            num_games=50,
            season="2023-24",
            include_playoffs=False,
        )

    def generate_large_simulation_dataset(self) -> dict[str, list]:
        """Generate a large dataset suitable for performance testing."""
        return self.generate_complete_dataset(
            num_teams=30,
            players_per_team=15,
            num_games=2000,  # Full season + playoffs
            season="2023-24",
            include_playoffs=True,
        )
