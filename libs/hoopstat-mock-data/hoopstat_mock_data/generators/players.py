"""Player generator for creating realistic NBA player data."""

import random

from faker import Faker

from ..models import Player, Position, Team


class PlayerGenerator:
    """Generator for NBA players with realistic attributes."""

    def __init__(self, seed: int = None):
        """Initialize the player generator with optional seed for reproducibility."""
        self.random = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            # Reset Faker seed each time to ensure reproducibility
            Faker.seed(seed)
            self.faker.seed_instance(seed)

    def generate_players(
        self, teams: list[Team], players_per_team: int = 15
    ) -> list[Player]:
        """
        Generate players for given teams.

        Args:
            teams: List of teams to generate players for
            players_per_team: Number of players per team (typical NBA roster is 12-15)

        Returns:
            List of Player models
        """
        players = []
        player_id = 1

        for team in teams:
            # Generate jersey numbers (1-99, no duplicates per team)
            available_numbers = list(range(1, 100))
            self.random.shuffle(available_numbers)

            for i in range(players_per_team):
                # Position distribution: more guards and forwards than centers
                position_weights = {
                    Position.POINT_GUARD: 0.2,
                    Position.SHOOTING_GUARD: 0.25,
                    Position.SMALL_FORWARD: 0.25,
                    Position.POWER_FORWARD: 0.2,
                    Position.CENTER: 0.1,
                }
                position = self.random.choices(
                    list(position_weights.keys()),
                    weights=list(position_weights.values()),
                )[0]

                # Generate realistic height and weight based on position
                height, weight = self._generate_height_weight(position)

                # Generate age and experience
                age = self.random.randint(19, 39)
                # Younger players tend to have less experience
                max_experience = min(age - 18, 20)
                years_experience = self.random.randint(0, max_experience)

                # Generate name
                first_name = self.faker.first_name_male()
                last_name = self.faker.last_name()
                full_name = f"{first_name} {last_name}"

                player = Player(
                    id=player_id,
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    team_id=team.id,
                    position=position,
                    jersey_number=available_numbers[i],
                    height_inches=height,
                    weight_pounds=weight,
                    age=age,
                    years_experience=years_experience,
                )
                players.append(player)
                player_id += 1

        return players

    def _generate_height_weight(self, position: Position) -> tuple[int, int]:
        """
        Generate realistic height and weight based on position.

        Returns:
            Tuple of (height_inches, weight_pounds)
        """
        # NBA average heights and weights by position (in inches and pounds)
        position_stats = {
            Position.POINT_GUARD: {
                "height_mean": 73,
                "height_std": 2,
                "weight_mean": 190,
                "weight_std": 15,
            },
            Position.SHOOTING_GUARD: {
                "height_mean": 76,
                "height_std": 2,
                "weight_mean": 205,
                "weight_std": 15,
            },
            Position.SMALL_FORWARD: {
                "height_mean": 78,
                "height_std": 2,
                "weight_mean": 220,
                "weight_std": 20,
            },
            Position.POWER_FORWARD: {
                "height_mean": 81,
                "height_std": 2,
                "weight_mean": 235,
                "weight_std": 20,
            },
            Position.CENTER: {
                "height_mean": 83,
                "height_std": 2,
                "weight_mean": 250,
                "weight_std": 25,
            },
        }

        stats = position_stats[position]

        # Generate height with normal distribution, constrained to realistic bounds
        height = int(
            self.random.normalvariate(stats["height_mean"], stats["height_std"])
        )
        height = max(60, min(96, height))  # 5'0" to 8'0"

        # Generate weight based on height and position
        weight = int(
            self.random.normalvariate(stats["weight_mean"], stats["weight_std"])
        )
        weight = max(150, min(350, weight))  # Realistic NBA weight range

        return height, weight

    def generate_single_player(
        self, team_id: int, position: Position = None, jersey_number: int = None
    ) -> Player:
        """
        Generate a single player.

        Args:
            team_id: ID of the team the player belongs to
            position: Specific position (random if None)
            jersey_number: Specific jersey number (random if None)

        Returns:
            Player model
        """
        if position is None:
            position = self.random.choice(list(Position))

        if jersey_number is None:
            jersey_number = self.random.randint(1, 99)

        height, weight = self._generate_height_weight(position)
        age = self.random.randint(19, 39)
        max_experience = min(age - 18, 20)
        years_experience = self.random.randint(0, max_experience)

        first_name = self.faker.first_name_male()
        last_name = self.faker.last_name()
        full_name = f"{first_name} {last_name}"

        return Player(
            id=1,  # Caller should set the appropriate ID
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            team_id=team_id,
            position=position,
            jersey_number=jersey_number,
            height_inches=height,
            weight_pounds=weight,
            age=age,
            years_experience=years_experience,
        )
