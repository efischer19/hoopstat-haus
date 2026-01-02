"""
Core processing logic for transforming Bronze layer data to Silver layer format.

This module contains the main processing classes and functions for:
- Loading Bronze layer JSON data from S3
- Validating and transforming data using Silver models
- Writing cleaned Silver layer data back to S3
"""

import json
from datetime import date
from typing import Any

import boto3
from hoopstat_data import (
    BoxScoreRaw,
    DataCleaningRulesEngine,
    DataLineage,
    GameStats,
    PlayerStats,
    TeamStats,
    ValidationMode,
    check_data_completeness,
    detect_outliers,
    normalize_team_name,
)
from hoopstat_observability import get_logger
from hoopstat_s3 import SilverS3Manager

logger = get_logger(__name__)


class BronzeToSilverProcessor:
    """Core processor for transforming Bronze layer data to Silver layer format."""

    def __init__(self, bronze_bucket: str, region_name: str = "us-east-1"):
        """
        Initialize the Bronze to Silver processor.

        Args:
            bronze_bucket: S3 bucket name where Bronze data is stored
            region_name: AWS region name
        """
        self.bronze_bucket = bronze_bucket
        self.region_name = region_name

        try:
            self.s3_client = boto3.client("s3", region_name=region_name)
            logger.info(
                f"Initialized Bronze-to-Silver processor for bucket: {bronze_bucket}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def read_bronze_json(self, entity: str, target_date: date) -> list[dict[str, Any]]:
        """
        Read Bronze JSON data from S3 (ADR-031: supports multiple files per date).

        Args:
            entity: Entity type (e.g., 'box')
            target_date: Date of the data

        Returns:
            List of parsed JSON data (one per file). Empty list if no files found.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        # ADR-032: Use URL-safe paths without 'date=' prefix
        prefix = f"raw/{entity}/{date_str}/"

        try:
            # List all objects under the date prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bronze_bucket, Prefix=prefix
            )

            if "Contents" not in response:
                logger.warning(
                    f"No Bronze data found at s3://{self.bronze_bucket}/{prefix}"
                )
                return []

            # Read each file and collect the data
            all_data = []
            for obj in response["Contents"]:
                key = obj["Key"]
                try:
                    file_response = self.s3_client.get_object(
                        Bucket=self.bronze_bucket, Key=key
                    )
                    json_content = file_response["Body"].read().decode("utf-8")
                    data = json.loads(json_content)
                    all_data.append(data)
                    logger.debug(
                        f"Successfully read Bronze data from s3://{self.bronze_bucket}/{key}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to read Bronze data from "
                        f"s3://{self.bronze_bucket}/{key}: {e}"
                    )
                    # Continue processing other files
                    continue

            logger.info(
                f"Successfully read {len(all_data)} Bronze files from "
                f"s3://{self.bronze_bucket}/{prefix}"
            )
            return all_data

        except Exception as e:
            logger.error(
                f"Failed to list Bronze data at s3://{self.bronze_bucket}/{prefix}: {e}"
            )
            raise

    def _map_nba_api_to_model(self, bronze_data: dict[str, Any]) -> dict[str, Any]:
        """
        Map NBA API camelCase format to snake_case model format.

        Handles the transformation from NBA API V3 format (boxScoreTraditional)
        to the BoxScoreRaw model's expected snake_case format.

        Args:
            bronze_data: Raw NBA API data (potentially with boxScoreTraditional wrapper)

        Returns:
            Mapped data in snake_case format compatible with BoxScoreRaw model
        """
        # Check if data is already in snake_case format (direct BoxScoreRaw format)
        # We check for home_team/away_team to distinguish from bronze data that might have game_id metadata
        if "home_team" in bronze_data or "away_team" in bronze_data:
            logger.debug("Data already in snake_case format, no mapping needed")
            return bronze_data

        # Check if data has boxScoreTraditional wrapper (NBA API V3 format)
        if "boxScoreTraditional" in bronze_data:
            logger.debug("Detected NBA API V3 format with boxScoreTraditional wrapper")
            box_score = bronze_data["boxScoreTraditional"]

            # Map top-level fields
            mapped_data = {
                "game_id": box_score.get("gameId"),
                "game_date": box_score.get("gameDate"),
                "arena": box_score.get("arena") or box_score.get("venue"),
            }

            # Map home team
            if "homeTeam" in box_score:
                home_team_data = box_score["homeTeam"]
                mapped_data["home_team"] = {
                    "id": home_team_data.get("teamId"),
                    "name": home_team_data.get("teamName"),
                    "city": home_team_data.get("teamCity"),
                    "abbreviation": home_team_data.get("teamTricode")
                    or home_team_data.get("teamSlug"),
                }

                # Map home team statistics
                if "statistics" in home_team_data:
                    mapped_data["home_team_stats"] = self._map_team_statistics(
                        home_team_data["statistics"]
                    )

                # Map home team players
                if "players" in home_team_data:
                    mapped_data["home_players"] = [
                        self._map_player_statistics(player, home_team_data)
                        for player in home_team_data["players"]
                    ]

            # Map away team
            if "awayTeam" in box_score:
                away_team_data = box_score["awayTeam"]
                mapped_data["away_team"] = {
                    "id": away_team_data.get("teamId"),
                    "name": away_team_data.get("teamName"),
                    "city": away_team_data.get("teamCity"),
                    "abbreviation": away_team_data.get("teamTricode")
                    or away_team_data.get("teamSlug"),
                }

                # Map away team statistics
                if "statistics" in away_team_data:
                    mapped_data["away_team_stats"] = self._map_team_statistics(
                        away_team_data["statistics"]
                    )

                # Map away team players
                if "players" in away_team_data:
                    mapped_data["away_players"] = [
                        self._map_player_statistics(player, away_team_data)
                        for player in away_team_data["players"]
                    ]

            return mapped_data

        # If no known format detected, return as-is and let validation catch any issues
        logger.warning("Unknown data format, returning as-is")
        return bronze_data

    def _map_team_statistics(self, stats: dict[str, Any]) -> dict[str, Any]:
        """Map team statistics from camelCase to snake_case."""
        return {
            "points": stats.get("points"),
            "field_goals_made": stats.get("fieldGoalsMade"),
            "field_goals_attempted": stats.get("fieldGoalsAttempted"),
            "three_pointers_made": stats.get("threePointersMade"),
            "three_pointers_attempted": stats.get("threePointersAttempted"),
            "free_throws_made": stats.get("freeThrowsMade"),
            "free_throws_attempted": stats.get("freeThrowsAttempted"),
            "offensive_rebounds": stats.get("reboundsOffensive"),
            "defensive_rebounds": stats.get("reboundsDefensive"),
            "rebounds": stats.get("reboundsTotal"),
            "assists": stats.get("assists"),
            "steals": stats.get("steals"),
            "blocks": stats.get("blocks"),
            "turnovers": stats.get("turnovers"),
            "fouls": stats.get("foulsPersonal"),
        }

    def _map_player_statistics(
        self, player: dict[str, Any], team_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Map player statistics from camelCase to snake_case."""
        stats = player.get("statistics", {})

        return {
            "player_id": player.get("personId"),
            "player_name": player.get("name") or player.get("nameI"),
            "team": team_data.get("teamName"),
            "position": player.get("position"),
            "minutes_played": stats.get("minutes") or stats.get("minutesCalculated"),
            "points": stats.get("points"),
            "offensive_rebounds": stats.get("reboundsOffensive"),
            "defensive_rebounds": stats.get("reboundsDefensive"),
            "assists": stats.get("assists"),
            "steals": stats.get("steals"),
            "blocks": stats.get("blocks"),
            "turnovers": stats.get("turnovers"),
            "field_goals_made": stats.get("fieldGoalsMade"),
            "field_goals_attempted": stats.get("fieldGoalsAttempted"),
            "three_pointers_made": stats.get("threePointersMade"),
            "three_pointers_attempted": stats.get("threePointersAttempted"),
            "free_throws_made": stats.get("freeThrowsMade"),
            "free_throws_attempted": stats.get("freeThrowsAttempted"),
        }

    def transform_to_silver(
        self, bronze_data: dict[str, Any], entity: str
    ) -> dict[str, list[dict]]:
        """
        Transform Bronze data to Silver models.

        Args:
            bronze_data: Raw Bronze layer data
            entity: Entity type

        Returns:
            Dictionary with lists of Silver model data organized by type
        """
        logger.info(f"Transforming Bronze data to Silver for entity: {entity}")

        # Map NBA API format to model format if needed
        mapped_data = self._map_nba_api_to_model(bronze_data)

        # Parse Bronze data using BoxScoreRaw model
        try:
            box_score_raw = BoxScoreRaw(**mapped_data)
        except Exception as e:
            logger.error(f"Failed to parse Bronze data with BoxScoreRaw model: {e}")
            raise ValueError(f"Invalid Bronze data format: {e}") from e

        # Initialize data cleaning rules engine
        try:
            rules_engine = DataCleaningRulesEngine()
        except Exception as e:
            logger.warning(
                f"Failed to initialize rules engine, proceeding without it: {e}"
            )
            rules_engine = None

        # Create data lineage
        lineage = DataLineage(
            source_system="bronze-to-silver-processor",
            schema_version="1.0.0",
            transformation_stage="silver",
            validation_mode=ValidationMode.STRICT,
        )

        silver_data = {
            "player_stats": [],
            "team_stats": [],
            "game_stats": [],
        }

        # Transform player statistics
        self._transform_player_stats(box_score_raw, silver_data, lineage, rules_engine)

        # Transform team statistics
        self._transform_team_stats(box_score_raw, silver_data, lineage, rules_engine)

        # Transform game statistics
        self._transform_game_stats(box_score_raw, silver_data, lineage, rules_engine)

        logger.info(
            f"Transformed to {len(silver_data['player_stats'])} player stats, "
            f"{len(silver_data['team_stats'])} team stats, "
            f"{len(silver_data['game_stats'])} game stats"
        )

        return silver_data

    def _transform_player_stats(
        self,
        box_score_raw: BoxScoreRaw,
        silver_data: dict,
        lineage: DataLineage,
        rules_engine: DataCleaningRulesEngine | None,
    ) -> None:
        """Transform player statistics from Bronze to Silver."""
        all_players = []
        if box_score_raw.home_players:
            all_players.extend(box_score_raw.home_players)
        if box_score_raw.away_players:
            all_players.extend(box_score_raw.away_players)

        for player_raw in all_players:
            try:
                # Apply data quality checks
                player_dict = player_raw.model_dump()
                completeness = check_data_completeness(player_dict)

                if completeness["completeness_ratio"] < 0.5:
                    logger.warning(
                        f"Low data completeness for player {player_raw.player_id}: "
                        f"{completeness['completeness_ratio']:.2f}"
                    )

                # Apply transformations
                team_name = player_raw.team
                if team_name:
                    team_name = normalize_team_name(
                        team_name, use_rules_engine=rules_engine is not None
                    )

                # Create PlayerStats with validation
                player_stats = PlayerStats(
                    player_id=str(player_raw.player_id or "unknown"),
                    player_name=player_raw.player_name,
                    team=team_name,
                    position=player_raw.position,
                    points=player_raw.points or 0,
                    rebounds=(player_raw.offensive_rebounds or 0)
                    + (player_raw.defensive_rebounds or 0),
                    assists=player_raw.assists or 0,
                    steals=player_raw.steals or 0,
                    blocks=player_raw.blocks or 0,
                    turnovers=player_raw.turnovers or 0,
                    field_goals_made=player_raw.field_goals_made,
                    field_goals_attempted=player_raw.field_goals_attempted,
                    three_pointers_made=player_raw.three_pointers_made,
                    three_pointers_attempted=player_raw.three_pointers_attempted,
                    free_throws_made=player_raw.free_throws_made,
                    free_throws_attempted=player_raw.free_throws_attempted,
                    minutes_played=self._convert_minutes_to_decimal(
                        player_raw.minutes_played
                    ),
                    game_id=str(box_score_raw.game_id)
                    if box_score_raw.game_id
                    else None,
                    lineage=lineage,
                )

                silver_data["player_stats"].append(player_stats.model_dump())

            except Exception as e:
                logger.error(f"Failed to transform player {player_raw.player_id}: {e}")
                # Continue processing other players
                continue

    def _transform_team_stats(
        self,
        box_score_raw: BoxScoreRaw,
        silver_data: dict,
        lineage: DataLineage,
        rules_engine: DataCleaningRulesEngine | None,
    ) -> None:
        """Transform team statistics from Bronze to Silver."""
        team_stats_list = []
        if box_score_raw.home_team_stats:
            team_stats_list.append(
                (box_score_raw.home_team_stats, box_score_raw.home_team)
            )
        if box_score_raw.away_team_stats:
            team_stats_list.append(
                (box_score_raw.away_team_stats, box_score_raw.away_team)
            )

        for team_stats_raw, team_raw in team_stats_list:
            try:
                # Apply transformations
                team_name = team_raw.name if team_raw else "Unknown"
                team_name = normalize_team_name(
                    team_name, use_rules_engine=rules_engine is not None
                )

                # Create TeamStats with validation
                team_stats = TeamStats(
                    team_id=str(team_raw.id) if team_raw and team_raw.id else "unknown",
                    team_name=team_name,
                    points=team_stats_raw.points or 0,
                    field_goals_made=team_stats_raw.field_goals_made or 0,
                    field_goals_attempted=team_stats_raw.field_goals_attempted or 0,
                    three_pointers_made=team_stats_raw.three_pointers_made,
                    three_pointers_attempted=team_stats_raw.three_pointers_attempted,
                    free_throws_made=team_stats_raw.free_throws_made,
                    free_throws_attempted=team_stats_raw.free_throws_attempted,
                    rebounds=(team_stats_raw.offensive_rebounds or 0)
                    + (team_stats_raw.defensive_rebounds or 0),
                    assists=team_stats_raw.assists or 0,
                    steals=team_stats_raw.steals,
                    blocks=team_stats_raw.blocks,
                    turnovers=team_stats_raw.turnovers,
                    fouls=team_stats_raw.fouls,
                    game_id=str(box_score_raw.game_id)
                    if box_score_raw.game_id
                    else None,
                    lineage=lineage,
                )

                silver_data["team_stats"].append(team_stats.model_dump())

            except Exception as e:
                logger.error(f"Failed to transform team stats: {e}")
                # Continue processing
                continue

    def _transform_game_stats(
        self,
        box_score_raw: BoxScoreRaw,
        silver_data: dict,
        lineage: DataLineage,
        rules_engine: DataCleaningRulesEngine | None,
    ) -> None:
        """Transform game statistics from Bronze to Silver."""
        try:
            # Get team IDs and scores from team stats
            home_team_id = (
                str(box_score_raw.home_team.id)
                if box_score_raw.home_team and box_score_raw.home_team.id
                else "unknown"
            )
            away_team_id = (
                str(box_score_raw.away_team.id)
                if box_score_raw.away_team and box_score_raw.away_team.id
                else "unknown"
            )

            home_score = (
                box_score_raw.home_team_stats.points
                if box_score_raw.home_team_stats
                else 0
            )
            away_score = (
                box_score_raw.away_team_stats.points
                if box_score_raw.away_team_stats
                else 0
            )

            # Create GameStats with validation
            game_stats = GameStats(
                game_id=str(box_score_raw.game_id)
                if box_score_raw.game_id
                else "unknown",
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_score=home_score,
                away_score=away_score,
                season=None,  # Season not available in BoxScoreRaw
                game_date=box_score_raw.game_date,
                venue=box_score_raw.arena,
                quarters=4,  # Default NBA quarters
                overtime=home_score == away_score
                if home_score and away_score
                else False,
                lineage=lineage,
            )

            silver_data["game_stats"].append(game_stats.model_dump())

        except Exception as e:
            logger.error(f"Failed to transform game stats: {e}")

    def _convert_minutes_to_decimal(self, minutes_str: str | None) -> float | None:
        """Convert minutes string (MM:SS) to decimal minutes."""
        if not minutes_str:
            return None

        try:
            if isinstance(minutes_str, int | float):
                return float(minutes_str)

            if ":" in str(minutes_str):
                parts = str(minutes_str).split(":")
                minutes = int(parts[0])
                seconds = int(parts[1]) if len(parts) > 1 else 0
                return minutes + (seconds / 60.0)
            else:
                return float(minutes_str)
        except (ValueError, IndexError):
            logger.warning(f"Failed to convert minutes: {minutes_str}")
            return None

    def apply_quality_checks(self, silver_data: dict[str, list]) -> dict[str, Any]:
        """
        Apply data quality checks to Silver data.

        Args:
            silver_data: Dictionary containing Silver model data

        Returns:
            Quality metrics and validation results
        """
        logger.info("Applying data quality checks to Silver data")

        quality_results = {
            "player_stats_quality": {},
            "team_stats_quality": {},
            "outliers": {},
            "overall_quality": True,
        }

        # Check player stats quality
        if silver_data.get("player_stats"):
            for i, player_stat in enumerate(silver_data["player_stats"]):
                completeness = check_data_completeness(player_stat)
                quality_results["player_stats_quality"][i] = completeness

                # Check for outliers in points
                if "points" in player_stat and player_stat["points"] is not None:
                    points_values = [
                        p.get("points", 0)
                        for p in silver_data["player_stats"]
                        if p.get("points") is not None
                    ]
                    if len(points_values) > 2:
                        outlier_indices = detect_outliers(points_values)
                        if i in outlier_indices:
                            quality_results["outliers"][f"player_{i}_points"] = (
                                player_stat["points"]
                            )

        # Check team stats quality
        if silver_data.get("team_stats"):
            for i, team_stat in enumerate(silver_data["team_stats"]):
                completeness = check_data_completeness(team_stat)
                quality_results["team_stats_quality"][i] = completeness

        # Determine overall quality
        player_quality_scores = [
            pq["completeness_ratio"]
            for pq in quality_results["player_stats_quality"].values()
        ]
        team_quality_scores = [
            tq["completeness_ratio"]
            for tq in quality_results["team_stats_quality"].values()
        ]

        avg_quality = 0.0
        if player_quality_scores or team_quality_scores:
            all_scores = player_quality_scores + team_quality_scores
            avg_quality = sum(all_scores) / len(all_scores)

        quality_results["overall_quality"] = avg_quality >= 0.7  # 70% threshold
        quality_results["average_completeness"] = avg_quality

        logger.info(
            f"Quality check complete: avg_completeness={avg_quality:.2f}, "
            f"outliers={len(quality_results['outliers'])}"
        )

        return quality_results


class SilverProcessor:
    """Main processor for transforming Bronze to Silver layer data."""

    def __init__(
        self, bronze_bucket: str | None = None, region_name: str = "us-east-1"
    ) -> None:
        """
        Initialize the Silver processor with dependencies.

        Args:
            bronze_bucket: S3 bucket name for Bronze data (optional for backward
                compatibility)
            region_name: AWS region name
        """
        self.bronze_bucket = bronze_bucket
        self.region_name = region_name

        if bronze_bucket:
            # Use SilverS3Manager for both Bronze reading and Silver writing
            self.s3_manager = SilverS3Manager(bronze_bucket, region_name=region_name)

            # Keep backward compatibility with existing BronzeToSilverProcessor
            self.bronze_to_silver_processor = BronzeToSilverProcessor(
                bronze_bucket, region_name
            )
        else:
            self.s3_manager = None
            self.bronze_to_silver_processor = None
            logger.warning(
                "No Bronze bucket configured - some operations may not be available"
            )

        logger.info("Silver processor initialized with SilverS3Manager")

    def process_date(self, target_date: date, dry_run: bool = False) -> bool:
        """
        Process all Bronze layer data for a specific date into Silver format.

        Args:
            target_date: The date to process
            dry_run: If True, validate but don't write data

        Returns:
            True if processing succeeded, False otherwise
        """
        logger.info(f"Processing Bronze data for {target_date}")

        try:
            if not self.bronze_to_silver_processor:
                logger.error("No Bronze bucket configured for processing")
                return False

            # Process box_scores entity (main entity type for now)
            entity = "box_scores"

            # 1. Load Bronze JSON data from S3 (ADR-031: returns list of games)
            bronze_data_list = self.bronze_to_silver_processor.read_bronze_json(
                entity, target_date
            )
            if not bronze_data_list:
                logger.warning(f"No Bronze data found for {entity} on {target_date}")
                return False

            logger.info(
                f"Found {len(bronze_data_list)} game(s) for {target_date}, "
                "processing each..."
            )

            # Aggregate all Silver data from all games
            all_silver_data = {
                "player_stats": [],
                "team_stats": [],
                "game_stats": [],
            }

            # 2. Process each game individually
            for i, bronze_data in enumerate(bronze_data_list):
                logger.debug(f"Processing game {i + 1}/{len(bronze_data_list)}")

                try:
                    # Transform to Silver models (PlayerStats, TeamStats, GameStats)
                    silver_data = self.bronze_to_silver_processor.transform_to_silver(
                        bronze_data, entity
                    )

                    # Aggregate the results
                    all_silver_data["player_stats"].extend(
                        silver_data.get("player_stats", [])
                    )
                    all_silver_data["team_stats"].extend(
                        silver_data.get("team_stats", [])
                    )
                    all_silver_data["game_stats"].extend(
                        silver_data.get("game_stats", [])
                    )

                except Exception as e:
                    logger.error(f"Failed to transform game {i + 1}: {e}")
                    # Continue processing other games
                    continue

            # 3. Validate aggregated data quality
            quality_results = self.bronze_to_silver_processor.apply_quality_checks(
                all_silver_data
            )

            if not quality_results.get("overall_quality", False):
                avg_completeness = quality_results.get("average_completeness", 0)
                logger.warning(
                    f"Data quality below threshold for {target_date}: "
                    f"avg_completeness={avg_completeness:.2f}"
                )

            # 4. Validate Silver data models
            if not self.validate_silver_data(all_silver_data):
                logger.error(f"Silver data validation failed for {target_date}")
                return False

            if dry_run:
                logger.info("Dry run mode - data validation only")
                player_count = len(all_silver_data.get("player_stats", []))
                team_count = len(all_silver_data.get("team_stats", []))
                game_count = len(all_silver_data.get("game_stats", []))
                logger.info(
                    f"Would process: {player_count} player stats, "
                    f"{team_count} team stats, {game_count} game stats"
                )
            else:
                logger.info("Processing and writing Silver layer data")

                # 5. Write Silver data to S3 using SilverS3Manager
                if self.s3_manager:
                    try:
                        written_keys = self.s3_manager.write_partitioned_silver_data(
                            all_silver_data, target_date, check_exists=True
                        )

                        player_count = len(all_silver_data.get("player_stats", []))
                        team_count = len(all_silver_data.get("team_stats", []))
                        game_count = len(all_silver_data.get("game_stats", []))

                        logger.info(
                            f"Successfully wrote Silver data for {target_date}: "
                            f"{player_count} player stats, {team_count} team stats, "
                            f"{game_count} game stats"
                        )
                        logger.info(
                            f"Written to S3 keys: {list(written_keys.values())}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to write Silver data to S3: {e}")
                        return False
                else:
                    logger.warning("No S3 manager configured - Silver data not written")
                    player_count = len(all_silver_data.get("player_stats", []))
                    team_count = len(all_silver_data.get("team_stats", []))
                    game_count = len(all_silver_data.get("game_stats", []))
                    logger.info(
                        f"Successfully processed: {player_count} player stats, "
                        f"{team_count} team stats, {game_count} game stats"
                    )

            return True

        except Exception as e:
            logger.error(f"Processing failed for {target_date}: {e}")
            return False

    def process_games(
        self, game_ids: list[str], dry_run: bool = False
    ) -> dict[str, bool]:
        """
        Process specific games from Bronze to Silver layer.

        Args:
            game_ids: List of game IDs to process
            dry_run: If True, validate but don't write data

        Returns:
            Dict mapping game_id to success status
        """
        results = {}

        for game_id in game_ids:
            try:
                # TODO: Implement game-specific processing in next PR
                logger.info(f"Processing game {game_id}")
                results[game_id] = True

            except Exception as e:
                logger.error(f"Failed to process game {game_id}: {e}")
                results[game_id] = False

        return results

    def validate_silver_data(self, silver_data: dict[str, list]) -> bool:
        """
        Validate Silver layer data against schema.

        Args:
            silver_data: The Silver layer data to validate

        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating Silver layer data")

        try:
            # Validate each player stats entry
            for i, player_data in enumerate(silver_data.get("player_stats", [])):
                try:
                    PlayerStats(**player_data)
                except Exception as e:
                    logger.error(f"Invalid player stats at index {i}: {e}")
                    return False

            # Validate each team stats entry
            for i, team_data in enumerate(silver_data.get("team_stats", [])):
                try:
                    TeamStats(**team_data)
                except Exception as e:
                    logger.error(f"Invalid team stats at index {i}: {e}")
                    return False

            # Validate each game stats entry
            for i, game_data in enumerate(silver_data.get("game_stats", [])):
                try:
                    GameStats(**game_data)
                except Exception as e:
                    logger.error(f"Invalid game stats at index {i}: {e}")
                    return False

            logger.info("Silver layer data validation successful")
            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
