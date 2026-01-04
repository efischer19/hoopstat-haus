"""
JSON artifact generation and S3 writing for Gold layer public serving.

This module provides utilities for generating small JSON artifacts from Gold analytics
data and writing them to the S3 served/ prefix for public consumption per ADR-028.
"""

import json
from datetime import date
from typing import Any

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError
from hoopstat_data.gold_models import GoldPlayerDailyStats, GoldTeamDailyStats
from hoopstat_observability import get_logger

logger = get_logger(__name__)


def _safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int, handling None and NaN.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if pd.isna(value) or value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class JSONArtifactWriter:
    """
    Writer for small JSON artifacts to S3 served/ prefix.

    Implements public serving layer per ADR-028:
    - served/player_daily/{date}/{player_id}.json
    - served/team_daily/{date}/{team_id}.json
    - served/top_lists/{date}/{metric}.json
    - served/latest.json
    """

    MAX_ARTIFACT_SIZE_KB = 100  # Per ADR-028, artifacts should be ≤100KB

    def __init__(self, gold_bucket: str, aws_region: str = "us-east-1") -> None:
        """
        Initialize the JSON artifact writer.

        Args:
            gold_bucket: S3 bucket for Gold layer data
            aws_region: AWS region for S3
        """
        self.gold_bucket = gold_bucket
        self.aws_region = aws_region
        self.s3_client = boto3.client("s3", region_name=aws_region)
        logger.info(f"Initialized JSON artifact writer for bucket: {gold_bucket}")

    def write_player_daily_artifacts(
        self, player_analytics: pd.DataFrame, target_date: date
    ) -> bool:
        """
        Write player daily JSON artifacts to S3.

        Creates individual JSON files for each player:
        served/player_daily/{date}/{player_id}.json

        Args:
            player_analytics: DataFrame with player analytics for the date
            target_date: Date being processed

        Returns:
            True if all writes succeeded, False otherwise
        """
        if player_analytics.empty:
            logger.info("No player analytics to write")
            return True

        date_str = target_date.strftime("%Y-%m-%d")
        success_count = 0
        error_count = 0

        logger.info(
            f"Writing {len(player_analytics)} player daily artifacts for {date_str}"
        )

        for _, row in player_analytics.iterrows():
            try:
                player_id = row.get("player_id")
                if not player_id:
                    logger.warning("Player row missing player_id, skipping")
                    continue

                # Convert row to dict and create Pydantic model for validation
                player_data = row.to_dict()

                # Use Pydantic model to serialize with validation
                # Note: GoldPlayerDailyStats expects specific field names
                model_data = self._prepare_player_daily_data(player_data, target_date)
                player_model = GoldPlayerDailyStats(**model_data)

                # Serialize to JSON using Pydantic
                json_content = player_model.model_dump_json(indent=2, exclude_none=True)

                # Check size constraint
                size_kb = len(json_content.encode("utf-8")) / 1024
                if size_kb > self.MAX_ARTIFACT_SIZE_KB:
                    logger.warning(
                        f"Player {player_id} artifact exceeds size limit: "
                        f"{size_kb:.1f}KB > {self.MAX_ARTIFACT_SIZE_KB}KB"
                    )

                # Write to S3
                s3_key = f"served/player_daily/{date_str}/{player_id}.json"
                self._upload_json_to_s3(json_content, s3_key)
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to write player daily artifact: {e}")
                error_count += 1

        logger.info(
            f"Wrote {success_count} player daily artifacts, {error_count} errors"
        )
        return error_count == 0

    def write_team_daily_artifacts(
        self, team_analytics: pd.DataFrame, target_date: date
    ) -> bool:
        """
        Write team daily JSON artifacts to S3.

        Creates individual JSON files for each team:
        served/team_daily/{date}/{team_id}.json

        Args:
            team_analytics: DataFrame with team analytics for the date
            target_date: Date being processed

        Returns:
            True if all writes succeeded, False otherwise
        """
        if team_analytics.empty:
            logger.info("No team analytics to write")
            return True

        date_str = target_date.strftime("%Y-%m-%d")
        success_count = 0
        error_count = 0

        logger.info(
            f"Writing {len(team_analytics)} team daily artifacts for {date_str}"
        )

        for _, row in team_analytics.iterrows():
            try:
                team_id = row.get("team_id")
                if not team_id:
                    logger.warning("Team row missing team_id, skipping")
                    continue

                # Convert row to dict and create Pydantic model
                team_data = row.to_dict()

                # Use Pydantic model to serialize with validation
                model_data = self._prepare_team_daily_data(team_data, target_date)
                team_model = GoldTeamDailyStats(**model_data)

                # Serialize to JSON using Pydantic
                json_content = team_model.model_dump_json(indent=2, exclude_none=True)

                # Check size constraint
                size_kb = len(json_content.encode("utf-8")) / 1024
                if size_kb > self.MAX_ARTIFACT_SIZE_KB:
                    logger.warning(
                        f"Team {team_id} artifact exceeds size limit: "
                        f"{size_kb:.1f}KB > {self.MAX_ARTIFACT_SIZE_KB}KB"
                    )

                # Write to S3
                s3_key = f"served/team_daily/{date_str}/{team_id}.json"
                self._upload_json_to_s3(json_content, s3_key)
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to write team daily artifact: {e}")
                error_count += 1

        logger.info(f"Wrote {success_count} team daily artifacts, {error_count} errors")
        return error_count == 0

    def write_top_lists(
        self, player_analytics: pd.DataFrame, target_date: date
    ) -> bool:
        """
        Write top lists JSON artifacts to S3.

        Creates JSON files for key metrics:
        served/top_lists/{date}/points.json
        served/top_lists/{date}/efficiency.json
        served/top_lists/{date}/true_shooting_pct.json

        Args:
            player_analytics: DataFrame with player analytics for the date
            target_date: Date being processed

        Returns:
            True if all writes succeeded, False otherwise
        """
        if player_analytics.empty:
            logger.info("No player analytics for top lists")
            return True

        date_str = target_date.strftime("%Y-%m-%d")
        success_count = 0
        error_count = 0

        # Define top lists to generate
        metrics = [
            ("points", "Points Leaders", 10),
            ("efficiency_rating", "Efficiency Leaders", 10),
            ("true_shooting_percentage", "True Shooting % Leaders", 10),
            ("assists", "Assists Leaders", 10),
            ("rebounds", "Rebounds Leaders", 10),
        ]

        for metric_field, metric_name, top_n in metrics:
            try:
                if metric_field not in player_analytics.columns:
                    logger.debug(f"Metric {metric_field} not available, skipping")
                    continue

                # Filter out null values and sort
                valid_data = player_analytics[
                    player_analytics[metric_field].notna()
                ].copy()

                if valid_data.empty:
                    continue

                top_players = valid_data.nlargest(top_n, metric_field)

                # Create top list structure
                top_list = {
                    "metric": metric_name,
                    "date": date_str,
                    "players": [
                        {
                            "rank": idx + 1,
                            "player_id": str(row.get("player_id", "")),
                            "player_name": row.get("player_name", ""),
                            "team": row.get("team", ""),
                            "value": float(row[metric_field]),
                        }
                        for idx, row in enumerate(top_players.to_dict("records"))
                    ],
                }

                json_content = json.dumps(top_list, indent=2)

                # Write to S3
                s3_key = f"served/top_lists/{date_str}/{metric_field}.json"
                self._upload_json_to_s3(json_content, s3_key)
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to write top list for {metric_field}: {e}")
                error_count += 1

        logger.info(f"Wrote {success_count} top lists, {error_count} errors")
        return error_count == 0

    def write_latest_index(self, target_date: date) -> bool:
        """
        Write latest.json index file to S3.

        Creates an index file with the most recent data availability:
        served/latest.json

        Args:
            target_date: Date being processed

        Returns:
            True if write succeeded, False otherwise
        """
        try:
            date_str = target_date.strftime("%Y-%m-%d")

            # Create index structure
            latest_index = {
                "latest_date": date_str,
                "available_data": {
                    "player_daily": f"served/player_daily/{date_str}/",
                    "team_daily": f"served/team_daily/{date_str}/",
                    "top_lists": f"served/top_lists/{date_str}/",
                },
                "updated_at": date.today().isoformat(),
            }

            json_content = json.dumps(latest_index, indent=2)

            # Write to S3
            s3_key = "served/latest.json"
            self._upload_json_to_s3(json_content, s3_key)

            logger.info(f"Wrote latest index for {date_str}")
            return True

        except Exception as e:
            logger.error(f"Failed to write latest index: {e}")
            return False

    def _prepare_player_daily_data(
        self, player_data: dict[str, Any], target_date: date
    ) -> dict[str, Any]:
        """
        Prepare player data for GoldPlayerDailyStats model.

        Args:
            player_data: Raw player analytics data
            target_date: Date being processed

        Returns:
            Prepared data dict for model initialization
        """
        # Map analytics DataFrame columns to model fields
        return {
            "player_id": str(player_data.get("player_id", "")),
            "player_name": player_data.get("player_name"),
            "team": player_data.get("team") or player_data.get("team_id"),
            "position": player_data.get("position"),
            "points": _safe_int(player_data.get("points")),
            "rebounds": _safe_int(player_data.get("rebounds")),
            "assists": _safe_int(player_data.get("assists")),
            "steals": _safe_int(player_data.get("steals")),
            "blocks": _safe_int(player_data.get("blocks")),
            "turnovers": _safe_int(player_data.get("turnovers")),
            "field_goals_made": _safe_int(player_data.get("field_goals_made")),
            "field_goals_attempted": _safe_int(
                player_data.get("field_goals_attempted")
            ),
            "three_pointers_made": _safe_int(player_data.get("three_pointers_made")),
            "three_pointers_attempted": _safe_int(
                player_data.get("three_pointers_attempted")
            ),
            "free_throws_made": _safe_int(player_data.get("free_throws_made")),
            "free_throws_attempted": _safe_int(
                player_data.get("free_throws_attempted")
            ),
            "minutes_played": player_data.get("minutes_played"),
            "game_id": player_data.get("game_id"),
            "game_date": target_date.strftime("%Y-%m-%d"),
            "efficiency_rating": player_data.get("efficiency_rating")
            or player_data.get("player_efficiency_rating"),
            "true_shooting_percentage": player_data.get("true_shooting_percentage")
            or player_data.get("true_shooting_pct"),
            "usage_rate": player_data.get("usage_rate"),
            "plus_minus": player_data.get("plus_minus"),
            "season": player_data.get("season"),
        }

    def _prepare_team_daily_data(
        self, team_data: dict[str, Any], target_date: date
    ) -> dict[str, Any]:
        """
        Prepare team data for GoldTeamDailyStats model.

        Args:
            team_data: Raw team analytics data
            target_date: Date being processed

        Returns:
            Prepared data dict for model initialization
        """
        return {
            "team_id": str(team_data.get("team_id", "")),
            "team_name": team_data.get("team_name", ""),
            "game_id": team_data.get("game_id"),
            "game_date": target_date.strftime("%Y-%m-%d"),
            "season": team_data.get("season"),
            "points": _safe_int(team_data.get("points")),
            "field_goals_made": _safe_int(team_data.get("field_goals_made")),
            "field_goals_attempted": _safe_int(team_data.get("field_goals_attempted")),
            "three_pointers_made": _safe_int(team_data.get("three_pointers_made")),
            "three_pointers_attempted": _safe_int(
                team_data.get("three_pointers_attempted")
            ),
            "free_throws_made": _safe_int(team_data.get("free_throws_made")),
            "free_throws_attempted": _safe_int(team_data.get("free_throws_attempted")),
            "rebounds": _safe_int(team_data.get("rebounds")),
            "assists": _safe_int(team_data.get("assists")),
            "steals": _safe_int(team_data.get("steals")),
            "blocks": _safe_int(team_data.get("blocks")),
            "turnovers": _safe_int(team_data.get("turnovers")),
            "fouls": _safe_int(team_data.get("fouls")),
            "offensive_rating": team_data.get("offensive_rating"),
            "defensive_rating": team_data.get("defensive_rating"),
            "pace": team_data.get("pace"),
            "true_shooting_percentage": team_data.get("true_shooting_percentage")
            or team_data.get("true_shooting_pct"),
            "opponent_team_id": team_data.get("opponent_team_id"),
            "home_game": team_data.get("home_game") or team_data.get("is_home"),
            "win": team_data.get("win"),
        }

    def _upload_json_to_s3(self, json_content: str, s3_key: str) -> None:
        """
        Upload JSON content to S3.

        Args:
            json_content: JSON string to upload
            s3_key: S3 key for the object

        Raises:
            Exception: If upload fails
        """
        try:
            self.s3_client.put_object(
                Bucket=self.gold_bucket,
                Key=s3_key,
                Body=json_content.encode("utf-8"),
                ContentType="application/json",
                CacheControl="public, max-age=3600",  # 1 hour cache
            )

            logger.debug(f"Uploaded JSON artifact to s3://{self.gold_bucket}/{s3_key}")

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to upload JSON to S3: {e}")
            raise
