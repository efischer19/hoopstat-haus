"""Schema validation utilities for generated NBA data."""

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from ..models import Game, Player, PlayerStats, Team, TeamStats


class SchemaValidator:
    """Validator for NBA data schemas."""

    # Mapping of data types to their corresponding Pydantic models
    MODEL_MAPPING = {
        "teams": Team,
        "players": Player,
        "games": Game,
        "player_stats": PlayerStats,
        "team_stats": TeamStats,
    }

    @classmethod
    def validate_data(
        cls, data: list[dict] | dict[str, list[dict]], data_type: str
    ) -> tuple[bool, list[str]]:
        """
        Validate data against the appropriate schema.

        Args:
            data: Data to validate
            data_type: Type of data (teams, players, games, etc.)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if data_type not in cls.MODEL_MAPPING:
            return False, [f"Unknown data type: {data_type}"]

        model_class = cls.MODEL_MAPPING[data_type]
        errors = []

        if isinstance(data, dict) and data_type in data:
            # Handle dictionary format
            data_list = data[data_type]
        elif isinstance(data, list):
            # Handle list format
            data_list = data
        else:
            return False, ["Invalid data format: expected list or dict"]

        for i, item in enumerate(data_list):
            try:
                model_class(**item)
            except ValidationError as e:
                errors.append(f"Item {i}: {str(e)}")

        return len(errors) == 0, errors

    @classmethod
    def validate_complete_dataset(
        cls, dataset: dict[str, list[dict]]
    ) -> tuple[bool, dict[str, list[str]]]:
        """
        Validate a complete dataset with multiple data types.

        Args:
            dataset: Dictionary containing different data types

        Returns:
            Tuple of (is_valid, dict_of_errors_by_type)
        """
        all_errors = {}
        is_valid = True

        for data_type, data_list in dataset.items():
            if data_type in cls.MODEL_MAPPING:
                valid, errors = cls.validate_data(data_list, data_type)
                if not valid:
                    is_valid = False
                    all_errors[data_type] = errors

        return is_valid, all_errors

    @classmethod
    def validate_relationships(
        cls, dataset: dict[str, list[dict]]
    ) -> tuple[bool, list[str]]:
        """
        Validate relationships between different data types.

        Args:
            dataset: Complete dataset

        Returns:
            Tuple of (is_valid, list_of_relationship_errors)
        """
        errors = []

        # Extract IDs for relationship validation
        team_ids = set()
        player_ids = set()
        game_ids = set()

        if "teams" in dataset:
            team_ids = {team["id"] for team in dataset["teams"]}

        if "players" in dataset:
            player_ids = {player["id"] for player in dataset["players"]}
            # Validate player team references
            for player in dataset["players"]:
                if player["team_id"] not in team_ids:
                    errors.append(
                        f"Player {player['id']} references non-existent "
                        f"team {player['team_id']}"
                    )

        if "games" in dataset:
            game_ids = {game["id"] for game in dataset["games"]}
            # Validate game team references
            for game in dataset["games"]:
                if game["home_team_id"] not in team_ids:
                    errors.append(
                        f"Game {game['id']} references non-existent "
                        f"home team {game['home_team_id']}"
                    )
                if game["away_team_id"] not in team_ids:
                    errors.append(
                        f"Game {game['id']} references non-existent "
                        f"away team {game['away_team_id']}"
                    )

        if "player_stats" in dataset:
            for stat in dataset["player_stats"]:
                if stat["player_id"] not in player_ids:
                    errors.append(
                        f"Player stat references non-existent "
                        f"player {stat['player_id']}"
                    )
                if stat["game_id"] not in game_ids:
                    errors.append(
                        f"Player stat references non-existent game {stat['game_id']}"
                    )
                if stat["team_id"] not in team_ids:
                    errors.append(
                        f"Player stat references non-existent team {stat['team_id']}"
                    )

        if "team_stats" in dataset:
            for stat in dataset["team_stats"]:
                if stat["team_id"] not in team_ids:
                    errors.append(
                        f"Team stat references non-existent team {stat['team_id']}"
                    )
                if stat["game_id"] not in game_ids:
                    errors.append(
                        f"Team stat references non-existent game {stat['game_id']}"
                    )

        return len(errors) == 0, errors

    @classmethod
    def validate_business_rules(
        cls, dataset: dict[str, list[dict]]
    ) -> tuple[bool, list[str]]:
        """
        Validate business rules specific to NBA data.

        Args:
            dataset: Complete dataset

        Returns:
            Tuple of (is_valid, list_of_business_rule_errors)
        """
        errors = []

        # Validate team constraints
        if "teams" in dataset:
            if len(dataset["teams"]) > 30:
                errors.append("Cannot have more than 30 NBA teams")

            # Check for unique team names and abbreviations
            names = [team["name"] for team in dataset["teams"]]
            abbrevs = [team["abbreviation"] for team in dataset["teams"]]

            if len(set(names)) != len(names):
                errors.append("Team names must be unique")
            if len(set(abbrevs)) != len(abbrevs):
                errors.append("Team abbreviations must be unique")

        # Validate player constraints
        if "players" in dataset:
            # Check jersey number uniqueness within teams
            team_jerseys = {}
            for player in dataset["players"]:
                team_id = player["team_id"]
                jersey = player["jersey_number"]

                if team_id not in team_jerseys:
                    team_jerseys[team_id] = set()

                if jersey in team_jerseys[team_id]:
                    errors.append(f"Duplicate jersey number {jersey} on team {team_id}")
                team_jerseys[team_id].add(jersey)

        # Validate game constraints
        if "games" in dataset:
            for game in dataset["games"]:
                if game["home_team_id"] == game["away_team_id"]:
                    errors.append(f"Game {game['id']}: team cannot play against itself")

                if game["is_completed"] and (
                    game["home_score"] is None or game["away_score"] is None
                ):
                    errors.append(f"Game {game['id']}: completed game must have scores")

        # Validate statistics constraints
        if "player_stats" in dataset:
            for stat in dataset["player_stats"]:
                # Field goals made cannot exceed attempted
                if stat["field_goals_made"] > stat["field_goals_attempted"]:
                    errors.append(
                        f"Player stat: field goals made ({stat['field_goals_made']}) > "
                        f"attempted ({stat['field_goals_attempted']})"
                    )

                # Three-pointers made cannot exceed attempted
                if stat["three_pointers_made"] > stat["three_pointers_attempted"]:
                    errors.append(
                        f"Player stat: three-pointers made "
                        f"({stat['three_pointers_made']}) > "
                        f"attempted ({stat['three_pointers_attempted']})"
                    )

                # Free throws made cannot exceed attempted
                if stat["free_throws_made"] > stat["free_throws_attempted"]:
                    errors.append(
                        f"Player stat: free throws made ({stat['free_throws_made']}) > "
                        f"attempted ({stat['free_throws_attempted']})"
                    )

        return len(errors) == 0, errors

    @classmethod
    def generate_validation_report(
        cls, dataset: dict[str, list[dict]]
    ) -> dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            dataset: Complete dataset to validate

        Returns:
            Dictionary containing validation results
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "dataset_summary": {},
            "schema_validation": {},
            "relationship_validation": {},
            "business_rule_validation": {},
            "overall_valid": True,
        }

        # Dataset summary
        for data_type, data_list in dataset.items():
            report["dataset_summary"][data_type] = len(data_list)

        # Schema validation
        schema_valid, schema_errors = cls.validate_complete_dataset(dataset)
        report["schema_validation"]["valid"] = schema_valid
        report["schema_validation"]["errors"] = schema_errors
        if not schema_valid:
            report["overall_valid"] = False

        # Relationship validation
        rel_valid, rel_errors = cls.validate_relationships(dataset)
        report["relationship_validation"]["valid"] = rel_valid
        report["relationship_validation"]["errors"] = rel_errors
        if not rel_valid:
            report["overall_valid"] = False

        # Business rule validation
        biz_valid, biz_errors = cls.validate_business_rules(dataset)
        report["business_rule_validation"]["valid"] = biz_valid
        report["business_rule_validation"]["errors"] = biz_errors
        if not biz_valid:
            report["overall_valid"] = False

        return report
