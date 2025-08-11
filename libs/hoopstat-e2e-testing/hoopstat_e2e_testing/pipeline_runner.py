"""
End-to-end pipeline test runner for medallion architecture.

Orchestrates the complete data pipeline testing from bronze → silver → gold layers.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from hoopstat_mock_data import MockDataGenerator

from .s3_utils import S3TestUtils

logger = logging.getLogger(__name__)


class PipelineTestRunner:
    """Orchestrates end-to-end pipeline testing."""

    def __init__(self, s3_utils: S3TestUtils, project_name: str = "test-hoopstat"):
        """
        Initialize pipeline test runner.

        Args:
            s3_utils: S3 utilities instance
            project_name: Project name for bucket naming
        """
        self.s3_utils = s3_utils
        self.project_name = project_name
        self.buckets = {}
        self.mock_generator = MockDataGenerator(seed=42)

    def setup_environment(self) -> bool:
        """
        Set up the testing environment with medallion architecture buckets.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up pipeline testing environment...")
            self.buckets = self.s3_utils.setup_medallion_buckets(self.project_name)

            # Verify all buckets were created
            for layer, bucket_name in self.buckets.items():
                if not self.s3_utils.bucket_exists(bucket_name):
                    logger.error(f"Failed to create {layer} bucket: {bucket_name}")
                    return False

            logger.info("Pipeline testing environment ready")
            return True
        except Exception as e:
            logger.error(f"Error setting up pipeline environment: {e}")
            return False

    def cleanup_environment(self) -> bool:
        """
        Clean up the testing environment.

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            logger.info("Cleaning up pipeline testing environment...")
            for _layer, bucket_name in self.buckets.items():
                if self.s3_utils.bucket_exists(bucket_name):
                    self.s3_utils.delete_bucket(bucket_name, delete_objects=True)

            logger.info("Pipeline testing environment cleaned up")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up pipeline environment: {e}")
            return False

    def ingest_bronze_data(
        self, num_teams: int = 4, num_players_per_team: int = 5
    ) -> bool:
        """
        Ingest raw mock data into the bronze layer as Parquet.

        Args:
            num_teams: Number of teams to generate
            num_players_per_team: Number of players per team

        Returns:
            True if ingestion successful, False otherwise
        """
        try:
            logger.info("Starting bronze layer data ingestion...")

            # Generate mock data
            dataset = self.mock_generator.generate_complete_dataset(
                num_teams=num_teams,
                players_per_team=num_players_per_team,
                num_games=10,
            )

            # Add ingestion metadata to each record
            ingestion_timestamp = datetime.utcnow().isoformat()

            # Convert teams to DataFrame and store as Parquet
            teams_data = []
            for team in dataset["teams"]:
                team_dict = team.model_dump()
                team_dict.update(
                    {
                        "ingestion_timestamp": ingestion_timestamp,
                        "source": "mock_generator",
                        "layer": "bronze",
                    }
                )
                teams_data.append(team_dict)

            teams_df = pd.DataFrame(teams_data)
            if not self.s3_utils.put_object(
                self.buckets["bronze"],
                "raw/teams/date=2023-12-25/data.parquet",
                teams_df,
            ):
                logger.error("Failed to upload teams data to bronze layer")
                return False

            # Convert players to DataFrame and store as Parquet
            players_data = []
            for player in dataset["players"]:
                player_dict = player.model_dump()
                player_dict.update(
                    {
                        "ingestion_timestamp": ingestion_timestamp,
                        "source": "mock_generator",
                        "layer": "bronze",
                    }
                )
                players_data.append(player_dict)

            players_df = pd.DataFrame(players_data)
            if not self.s3_utils.put_object(
                self.buckets["bronze"],
                "raw/players/date=2023-12-25/data.parquet",
                players_df,
            ):
                logger.error("Failed to upload players data to bronze layer")
                return False

            # Convert games to DataFrame and store as Parquet
            games_data = []
            for game in dataset["games"]:
                game_dict = game.model_dump()
                game_dict.update(
                    {
                        "ingestion_timestamp": ingestion_timestamp,
                        "source": "mock_generator",
                        "layer": "bronze",
                    }
                )
                games_data.append(game_dict)

            games_df = pd.DataFrame(games_data)
            if not self.s3_utils.put_object(
                self.buckets["bronze"],
                "raw/games/date=2023-12-25/data.parquet",
                games_df,
            ):
                logger.error("Failed to upload games data to bronze layer")
                return False

            logger.info(
                f"Bronze layer ingestion complete: {len(dataset['teams'])} teams, "
                f"{len(dataset['players'])} players, {len(dataset['games'])} games"
            )
            return True

        except Exception as e:
            logger.error(f"Error ingesting bronze data: {e}")
            return False

    def transform_silver_data(self) -> bool:
        """
        Transform bronze data into silver layer (cleaned and normalized).

        Returns:
            True if transformation successful, False otherwise
        """
        try:
            logger.info("Starting silver layer data transformation...")

            # Read bronze data from Parquet files
            teams_df = self.s3_utils.get_object(
                self.buckets["bronze"],
                "raw/teams/date=2023-12-25/data.parquet",
                "dataframe",
            )
            players_df = self.s3_utils.get_object(
                self.buckets["bronze"],
                "raw/players/date=2023-12-25/data.parquet",
                "dataframe",
            )
            games_df = self.s3_utils.get_object(
                self.buckets["bronze"],
                "raw/games/date=2023-12-25/data.parquet",
                "dataframe",
            )

            if any(df is None for df in [teams_df, players_df, games_df]):
                logger.error("Failed to read bronze layer data")
                return False

            # Apply transformations (simulate data cleaning)
            transformation_timestamp = datetime.utcnow().isoformat()

            # Clean and normalize teams data
            teams_df["full_name"] = teams_df["city"] + " " + teams_df["name"]
            teams_df["created_at"] = transformation_timestamp

            # Clean and normalize players data
            players_df["full_name"] = (
                players_df["first_name"] + " " + players_df["last_name"]
            )
            height_meters = players_df["height_inches"] * 2.54 / 100
            weight_kg = players_df["weight_pounds"] * 0.453592
            players_df["bmi"] = weight_kg / (height_meters**2)
            players_df["created_at"] = transformation_timestamp

            # Clean games data
            games_df["game_date"] = pd.to_datetime(
                games_df["game_date"]
            ).dt.date.astype(str)
            games_df["total_score"] = games_df["home_score"] + games_df["away_score"]
            games_df["created_at"] = transformation_timestamp

            # Store cleaned data as Parquet in silver layer
            if not self.s3_utils.put_object(
                self.buckets["silver"], "cleaned/teams/teams.parquet", teams_df
            ):
                logger.error("Failed to upload cleaned teams data to silver layer")
                return False

            if not self.s3_utils.put_object(
                self.buckets["silver"], "cleaned/players/players.parquet", players_df
            ):
                logger.error("Failed to upload cleaned players data to silver layer")
                return False

            if not self.s3_utils.put_object(
                self.buckets["silver"], "cleaned/games/games.parquet", games_df
            ):
                logger.error("Failed to upload cleaned games data to silver layer")
                return False

            logger.info("Silver layer transformation complete")
            return True

        except Exception as e:
            logger.error(f"Error transforming silver data: {e}")
            return False

    def aggregate_gold_data(self) -> bool:
        """
        Aggregate silver data into gold layer (business metrics).

        Returns:
            True if aggregation successful, False otherwise
        """
        try:
            logger.info("Starting gold layer data aggregation...")

            # Read silver data
            teams_df = self.s3_utils.get_object(
                self.buckets["silver"], "cleaned/teams/teams.parquet", "dataframe"
            )
            players_df = self.s3_utils.get_object(
                self.buckets["silver"], "cleaned/players/players.parquet", "dataframe"
            )
            games_df = self.s3_utils.get_object(
                self.buckets["silver"], "cleaned/games/games.parquet", "dataframe"
            )

            if any(df is None for df in [teams_df, players_df, games_df]):
                logger.error("Failed to read silver layer data")
                return False

            aggregation_timestamp = datetime.utcnow().isoformat()

            # Calculate team statistics
            team_stats = []
            for _, team in teams_df.iterrows():
                team_games = games_df[
                    (games_df["home_team_id"] == team["id"])
                    | (games_df["away_team_id"] == team["id"])
                ]

                wins = 0
                total_points = 0
                for _, game in team_games.iterrows():
                    if game["home_team_id"] == team["id"]:
                        total_points += game["home_score"]
                        if game["home_score"] > game["away_score"]:
                            wins += 1
                    else:
                        total_points += game["away_score"]
                        if game["away_score"] > game["home_score"]:
                            wins += 1

                wins_pct = wins / len(team_games) if len(team_games) > 0 else 0
                avg_ppg = total_points / len(team_games) if len(team_games) > 0 else 0

                team_stats.append(
                    {
                        "team_id": team["id"],
                        "team_name": team["full_name"],
                        "games_played": len(team_games),
                        "wins": wins,
                        "losses": len(team_games) - wins,
                        "win_percentage": wins_pct,
                        "total_points": total_points,
                        "avg_points_per_game": avg_ppg,
                        "created_at": aggregation_timestamp,
                    }
                )

            team_stats_df = pd.DataFrame(team_stats)

            # Calculate player statistics
            player_stats = []
            for _, player in players_df.iterrows():
                player_stats.append(
                    {
                        "player_id": player["id"],
                        "player_name": player["full_name"],
                        "team_id": player["team_id"],
                        "position": player["position"],
                        "height_cm": player["height_inches"] * 2.54,
                        "weight_kg": player["weight_pounds"] * 0.453592,
                        "bmi": player["bmi"],
                        "jersey_number": player["jersey_number"],
                        "created_at": aggregation_timestamp,
                    }
                )

            player_stats_df = pd.DataFrame(player_stats)

            # Calculate league summary
            league_summary = {
                "total_teams": len(teams_df),
                "total_players": len(players_df),
                "total_games": len(games_df),
                "avg_points_per_game": games_df["total_score"].mean(),
                "highest_scoring_game": games_df["total_score"].max(),
                "created_at": aggregation_timestamp,
            }

            # Store aggregated data in gold layer
            if not self.s3_utils.put_object(
                self.buckets["gold"], "metrics/team_stats.parquet", team_stats_df
            ):
                logger.error("Failed to upload team stats to gold layer")
                return False

            if not self.s3_utils.put_object(
                self.buckets["gold"], "metrics/player_stats.parquet", player_stats_df
            ):
                logger.error("Failed to upload player stats to gold layer")
                return False

            if not self.s3_utils.put_object(
                self.buckets["gold"], "metrics/league_summary.json", league_summary
            ):
                logger.error("Failed to upload league summary to gold layer")
                return False

            logger.info("Gold layer aggregation complete")
            return True

        except Exception as e:
            logger.error(f"Error aggregating gold data: {e}")
            return False

    def run_full_pipeline(
        self, num_teams: int = 4, num_players_per_team: int = 5
    ) -> bool:
        """
        Run the complete pipeline test from bronze to gold.

        Args:
            num_teams: Number of teams to generate
            num_players_per_team: Number of players per team

        Returns:
            True if entire pipeline completed successfully, False otherwise
        """
        try:
            logger.info("Starting full pipeline test...")

            # Setup environment
            if not self.setup_environment():
                return False

            # Run pipeline stages
            stages = [
                (
                    "bronze ingestion",
                    lambda: self.ingest_bronze_data(num_teams, num_players_per_team),
                ),
                ("silver transformation", self.transform_silver_data),
                ("gold aggregation", self.aggregate_gold_data),
            ]

            for stage_name, stage_func in stages:
                logger.info(f"Running {stage_name}...")
                if not stage_func():
                    logger.error(f"Pipeline failed at {stage_name}")
                    return False
                logger.info(f"Completed {stage_name}")

            logger.info("Full pipeline test completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error running full pipeline: {e}")
            return False

    def verify_pipeline_output(self) -> dict[str, Any]:
        """
        Verify the pipeline output and return validation results.

        Returns:
            Dictionary with validation results
        """
        results = {
            "bronze_layer": {"status": "unknown", "details": {}},
            "silver_layer": {"status": "unknown", "details": {}},
            "gold_layer": {"status": "unknown", "details": {}},
        }

        try:
            # Verify bronze layer
            bronze_objects = [
                "raw/teams/date=2023-12-25/data.parquet",
                "raw/players/date=2023-12-25/data.parquet",
                "raw/games/date=2023-12-25/data.parquet",
            ]

            bronze_valid = True
            bronze_details = {}
            for obj_key in bronze_objects:
                obj_exists = (
                    self.s3_utils.get_object(
                        self.buckets["bronze"], obj_key, "dataframe"
                    )
                    is not None
                )
                bronze_details[obj_key] = obj_exists
                if not obj_exists:
                    bronze_valid = False

            results["bronze_layer"]["status"] = "valid" if bronze_valid else "invalid"
            results["bronze_layer"]["details"] = bronze_details

            # Verify silver layer
            silver_objects = [
                "cleaned/teams/teams.parquet",
                "cleaned/players/players.parquet",
                "cleaned/games/games.parquet",
            ]

            silver_valid = True
            silver_details = {}
            for obj_key in silver_objects:
                obj_exists = (
                    self.s3_utils.get_object(
                        self.buckets["silver"], obj_key, "dataframe"
                    )
                    is not None
                )
                silver_details[obj_key] = obj_exists
                if not obj_exists:
                    silver_valid = False

            results["silver_layer"]["status"] = "valid" if silver_valid else "invalid"
            results["silver_layer"]["details"] = silver_details

            # Verify gold layer
            gold_objects = [
                "metrics/team_stats.parquet",
                "metrics/player_stats.parquet",
                "metrics/league_summary.json",
            ]

            gold_valid = True
            gold_details = {}
            for obj_key in gold_objects:
                if obj_key.endswith(".json"):
                    obj_exists = bool(
                        self.s3_utils.get_object(self.buckets["gold"], obj_key, "json")
                    )
                else:
                    obj_exists = (
                        self.s3_utils.get_object(
                            self.buckets["gold"], obj_key, "dataframe"
                        )
                        is not None
                    )
                gold_details[obj_key] = obj_exists
                if not obj_exists:
                    gold_valid = False

            results["gold_layer"]["status"] = "valid" if gold_valid else "invalid"
            results["gold_layer"]["details"] = gold_details

        except Exception as e:
            logger.error(f"Error verifying pipeline output: {e}")
            for layer in results:
                results[layer]["status"] = "error"
                results[layer]["error"] = str(e)

        return results
