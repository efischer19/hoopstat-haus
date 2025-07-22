"""Game generator for creating NBA game schedules and results."""

import random
from datetime import datetime, timedelta

from ..models import Game, GameType, Team


class GameGenerator:
    """Generator for NBA games with realistic schedules and scores."""

    def __init__(self, seed: int = None):
        """Initialize the game generator with optional seed for reproducibility."""
        self.random = random.Random(seed)

    def generate_season_schedule(
        self, teams: list[Team], season: str = "2023-24", include_playoffs: bool = True
    ) -> list[Game]:
        """
        Generate a full NBA season schedule.

        Args:
            teams: List of teams
            season: Season string (e.g., "2023-24")
            include_playoffs: Whether to include playoff games

        Returns:
            List of Game models
        """
        if len(teams) != 30:
            raise ValueError("NBA schedule generation requires exactly 30 teams")

        games = []
        game_id = 1

        # Generate regular season (82 games per team)
        regular_season_games = self._generate_regular_season(teams, season, game_id)
        games.extend(regular_season_games)
        game_id += len(regular_season_games)

        if include_playoffs:
            # Generate playoffs (simplified 16-team playoff)
            playoff_games = self._generate_playoffs(teams, season, game_id)
            games.extend(playoff_games)

        return games

    def generate_games(
        self,
        teams: list[Team],
        count: int,
        season: str = "2023-24",
        game_type: GameType = GameType.REGULAR_SEASON,
    ) -> list[Game]:
        """
        Generate a specific number of random games.

        Args:
            teams: List of teams
            count: Number of games to generate
            season: Season string
            game_type: Type of games to generate

        Returns:
            List of Game models
        """
        games = []

        # Start date for the season
        start_date = self._get_season_start_date(season)

        for i in range(count):
            # Random matchup
            home_team, away_team = self.random.sample(teams, 2)

            # Random date within the season
            days_offset = self.random.randint(0, 180)  # ~6 month season
            game_date = start_date + timedelta(days=days_offset)

            # Generate realistic game time (7-10 PM local time)
            hour = self.random.randint(19, 22)
            minute = self.random.choice([0, 30])
            game_date = game_date.replace(hour=hour, minute=minute)

            # Generate scores if game is completed
            is_completed = self.random.choice([True, False])
            home_score, away_score = None, None
            if is_completed:
                home_score, away_score = self._generate_realistic_scores()

            game = Game(
                id=i + 1,
                season=season,
                game_date=game_date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=home_score,
                away_score=away_score,
                game_type=game_type,
                is_completed=is_completed,
            )
            games.append(game)

        return games

    def _generate_regular_season(
        self, teams: list[Team], season: str, start_id: int
    ) -> list[Game]:
        """Generate regular season schedule (simplified)."""
        games = []
        game_id = start_id
        start_date = self._get_season_start_date(season)

        # Simplified schedule: each team plays every other team 2-3 times
        # This generates approximately 82 games per team
        for i, team1 in enumerate(teams):
            for j, team2 in enumerate(teams):
                if i >= j:  # Avoid duplicates
                    continue

                # Teams play 2-4 games against each other
                games_between = 2
                if team1.conference == team2.conference:
                    games_between = 3  # More games within conference
                if team1.division == team2.division:
                    games_between = 4  # Most games within division

                for game_num in range(games_between):
                    # Alternate home/away
                    if game_num % 2 == 0:
                        home_team, away_team = team1, team2
                    else:
                        home_team, away_team = team2, team1

                    # Spread games throughout the season
                    days_offset = (game_id * 2) % 180  # Spread over ~6 months
                    game_date = start_date + timedelta(days=days_offset)

                    # Most games are completed
                    is_completed = self.random.choice([True, True, True, False])
                    home_score, away_score = None, None
                    if is_completed:
                        home_score, away_score = self._generate_realistic_scores()

                    game = Game(
                        id=game_id,
                        season=season,
                        game_date=game_date,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        home_score=home_score,
                        away_score=away_score,
                        game_type=GameType.REGULAR_SEASON,
                        is_completed=is_completed,
                    )
                    games.append(game)
                    game_id += 1

        return games

    def _generate_playoffs(
        self, teams: list[Team], season: str, start_id: int
    ) -> list[Game]:
        """Generate playoff games (simplified bracket)."""
        games = []
        game_id = start_id

        # Simplified playoffs: top 8 teams from each conference
        playoff_start = self._get_season_start_date(season) + timedelta(days=200)

        # Generate some playoff games (simplified)
        playoff_teams = self.random.sample(teams, 16)  # 8 from each conference

        for i in range(0, len(playoff_teams), 2):
            if i + 1 < len(playoff_teams):
                team1, team2 = playoff_teams[i], playoff_teams[i + 1]

                # Best of 7 series (generate 4-7 games)
                series_length = self.random.randint(4, 7)

                for game_num in range(series_length):
                    # Alternate home court
                    if game_num % 2 == 0:
                        home_team, away_team = team1, team2
                    else:
                        home_team, away_team = team2, team1

                    game_date = playoff_start + timedelta(days=game_num * 2)
                    home_score, away_score = self._generate_realistic_scores()

                    game = Game(
                        id=game_id,
                        season=season,
                        game_date=game_date,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        home_score=home_score,
                        away_score=away_score,
                        game_type=GameType.PLAYOFFS,
                        is_completed=True,
                    )
                    games.append(game)
                    game_id += 1

        return games

    def _generate_realistic_scores(self) -> tuple[int, int]:
        """Generate realistic NBA game scores."""
        # NBA games typically score 90-130 points
        home_score = self.random.randint(85, 135)
        away_score = self.random.randint(85, 135)

        # Home court advantage (slight boost)
        if self.random.random() < 0.6:  # 60% chance home team has advantage
            home_score += self.random.randint(0, 8)

        return home_score, away_score

    def _get_season_start_date(self, season: str) -> datetime:
        """Get the start date for a given season."""
        # Parse season string like "2023-24"
        start_year = int(season.split("-")[0])

        # NBA season typically starts in October
        return datetime(start_year, 10, 15)
