"""Statistics generator for creating realistic NBA player and team statistics."""

import random

import numpy as np

from ..models import Game, Player, PlayerStats, Position, TeamStats


class StatisticsGenerator:
    """Generator for NBA statistics with realistic distributions."""

    def __init__(self, seed: int = None):
        """Initialize the statistics generator with optional seed for reproducibility."""
        self.random = random.Random(seed)
        if seed is not None:
            np.random.seed(seed)
        self.np_random = np.random

    def generate_player_stats(
        self, players: list[Player], games: list[Game]
    ) -> list[PlayerStats]:
        """
        Generate player statistics for games.

        Args:
            players: List of players
            games: List of games

        Returns:
            List of PlayerStats models
        """
        all_stats = []

        for game in games:
            if not game.is_completed:
                continue  # Skip unfinished games

            # Get players for both teams
            home_players = [p for p in players if p.team_id == game.home_team_id]
            away_players = [p for p in players if p.team_id == game.away_team_id]

            # Generate stats for home team
            home_stats = self._generate_team_game_stats(
                home_players, game, is_home=True
            )
            all_stats.extend(home_stats)

            # Generate stats for away team
            away_stats = self._generate_team_game_stats(
                away_players, game, is_home=False
            )
            all_stats.extend(away_stats)

        return all_stats

    def generate_team_stats(self, player_stats: list[PlayerStats]) -> list[TeamStats]:
        """
        Generate team statistics by aggregating player statistics.

        Args:
            player_stats: List of player statistics

        Returns:
            List of TeamStats models
        """
        team_stats = {}

        # Group player stats by team and game
        for stat in player_stats:
            key = (stat.team_id, stat.game_id)
            if key not in team_stats:
                team_stats[key] = []
            team_stats[key].append(stat)

        # Aggregate team statistics
        aggregated_stats = []
        for (team_id, game_id), stats_list in team_stats.items():
            team_stat = self._aggregate_team_stats(team_id, game_id, stats_list)
            aggregated_stats.append(team_stat)

        return aggregated_stats

    def _generate_team_game_stats(
        self, team_players: list[Player], game: Game, is_home: bool
    ) -> list[PlayerStats]:
        """Generate statistics for all players on a team for a single game."""
        stats = []

        # Determine total team minutes (48 minutes * 5 positions)
        total_minutes = 240

        # Distribute minutes among players
        minutes_distribution = self._distribute_minutes(team_players, total_minutes)

        for player, minutes in zip(team_players, minutes_distribution, strict=False):
            if minutes > 0:  # Only generate stats for players who played
                player_stat = self._generate_single_player_stats(
                    player, game, minutes, is_home
                )
                stats.append(player_stat)

        return stats

    def _distribute_minutes(
        self, players: list[Player], total_minutes: int
    ) -> list[float]:
        """Distribute playing minutes among team players."""
        # Sort players by a rough "skill" estimate (based on experience)
        sorted_players = sorted(
            players,
            key=lambda p: p.years_experience + self.random.randint(0, 5),
            reverse=True,
        )

        minutes = []
        remaining_minutes = total_minutes

        for i, player in enumerate(sorted_players):
            if i < 8:  # Top 8 players get significant minutes
                if i < 5:  # Starters get most minutes
                    player_minutes = self.random.uniform(28, 42)
                else:  # Bench players
                    player_minutes = self.random.uniform(15, 30)
            elif i < 12:  # Deep bench gets some minutes
                player_minutes = self.random.uniform(0, 15)
            else:  # End of bench rarely plays
                player_minutes = 0

            # Ensure we don't exceed total minutes
            player_minutes = min(player_minutes, remaining_minutes)
            minutes.append(player_minutes)
            remaining_minutes -= player_minutes

        # Reorder minutes to match original player order
        player_indices = {id(p): i for i, p in enumerate(players)}
        reordered_minutes = [0] * len(players)
        for player, minute in zip(sorted_players, minutes, strict=False):
            original_index = player_indices[id(player)]
            reordered_minutes[original_index] = minute

        return reordered_minutes

    def _generate_single_player_stats(
        self, player: Player, game: Game, minutes: float, is_home: bool
    ) -> PlayerStats:
        """Generate statistics for a single player in a game."""
        # Base rates per minute by position
        position_rates = {
            Position.POINT_GUARD: {
                "points_per_min": 0.35,
                "rebounds_per_min": 0.08,
                "assists_per_min": 0.15,
                "fg_rate": 0.45,
                "three_rate": 0.35,
                "ft_rate": 0.80,
            },
            Position.SHOOTING_GUARD: {
                "points_per_min": 0.40,
                "rebounds_per_min": 0.10,
                "assists_per_min": 0.08,
                "fg_rate": 0.47,
                "three_rate": 0.38,
                "ft_rate": 0.82,
            },
            Position.SMALL_FORWARD: {
                "points_per_min": 0.38,
                "rebounds_per_min": 0.15,
                "assists_per_min": 0.10,
                "fg_rate": 0.48,
                "three_rate": 0.36,
                "ft_rate": 0.78,
            },
            Position.POWER_FORWARD: {
                "points_per_min": 0.35,
                "rebounds_per_min": 0.20,
                "assists_per_min": 0.06,
                "fg_rate": 0.52,
                "three_rate": 0.32,
                "ft_rate": 0.75,
            },
            Position.CENTER: {
                "points_per_min": 0.32,
                "rebounds_per_min": 0.25,
                "assists_per_min": 0.04,
                "fg_rate": 0.55,
                "three_rate": 0.25,
                "ft_rate": 0.70,
            },
        }

        rates = position_rates[player.position]

        # Generate basic stats based on minutes played
        expected_points = minutes * rates["points_per_min"]
        expected_rebounds = minutes * rates["rebounds_per_min"]
        expected_assists = minutes * rates["assists_per_min"]

        # Add some randomness
        points = max(
            0, int(self.random.normalvariate(expected_points, expected_points * 0.3))
        )
        rebounds = max(
            0,
            int(self.random.normalvariate(expected_rebounds, expected_rebounds * 0.4)),
        )
        assists = max(
            0, int(self.random.normalvariate(expected_assists, expected_assists * 0.4))
        )

        # Generate shooting stats
        # Estimate field goal attempts based on points and position
        estimated_fga = points / 2.2  # Rough estimate
        fga = max(0, int(self.random.normalvariate(estimated_fga, estimated_fga * 0.3)))
        fgm = int(fga * rates["fg_rate"] * self.random.uniform(0.7, 1.3))
        fgm = min(fgm, fga)  # Can't make more than attempted

        # Three-pointers (subset of field goals)
        three_attempt_rate = (
            0.4
            if player.position in [Position.POINT_GUARD, Position.SHOOTING_GUARD]
            else 0.2
        )
        tpa = int(fga * three_attempt_rate)
        tpm = int(tpa * rates["three_rate"] * self.random.uniform(0.7, 1.3))
        tpm = min(tpm, tpa)

        # Free throws
        lambda_param = 2.5 if minutes > 20 else 1.0
        ft_attempts = max(0, self.np_random.poisson(lambda_param))
        ftm = int(ft_attempts * rates["ft_rate"] * self.random.uniform(0.8, 1.2))
        ftm = min(ftm, ft_attempts)

        # Other stats
        steals = max(0, self.np_random.poisson(minutes * 0.03))
        blocks = max(0, self.np_random.poisson(minutes * 0.02))
        turnovers = max(0, self.np_random.poisson(minutes * 0.06))
        fouls = max(0, min(6, self.np_random.poisson(minutes * 0.08)))

        return PlayerStats(
            player_id=player.id,
            game_id=game.id,
            team_id=player.team_id,
            minutes_played=round(minutes, 1),
            points=points,
            rebounds=rebounds,
            assists=assists,
            steals=steals,
            blocks=blocks,
            turnovers=turnovers,
            fouls=fouls,
            field_goals_made=fgm,
            field_goals_attempted=fga,
            three_pointers_made=tpm,
            three_pointers_attempted=tpa,
            free_throws_made=ftm,
            free_throws_attempted=ft_attempts,
        )

    def _aggregate_team_stats(
        self, team_id: int, game_id: int, player_stats: list[PlayerStats]
    ) -> TeamStats:
        """Aggregate individual player stats into team statistics."""
        return TeamStats(
            team_id=team_id,
            game_id=game_id,
            points=sum(stat.points for stat in player_stats),
            rebounds=sum(stat.rebounds for stat in player_stats),
            assists=sum(stat.assists for stat in player_stats),
            steals=sum(stat.steals for stat in player_stats),
            blocks=sum(stat.blocks for stat in player_stats),
            turnovers=sum(stat.turnovers for stat in player_stats),
            fouls=sum(stat.fouls for stat in player_stats),
            field_goals_made=sum(stat.field_goals_made for stat in player_stats),
            field_goals_attempted=sum(
                stat.field_goals_attempted for stat in player_stats
            ),
            three_pointers_made=sum(stat.three_pointers_made for stat in player_stats),
            three_pointers_attempted=sum(
                stat.three_pointers_attempted for stat in player_stats
            ),
            free_throws_made=sum(stat.free_throws_made for stat in player_stats),
            free_throws_attempted=sum(
                stat.free_throws_attempted for stat in player_stats
            ),
        )
