"""
Player statistics aggregator module.

This module contains the core business logic for aggregating Silver layer
player game data into Gold layer daily and season-to-date statistics.
"""

import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from app.config import LambdaConfig
from app.s3_utils import S3Client
from app.validation import validate_input_data, validate_output_data

logger = logging.getLogger(__name__)


class PlayerStatsAggregator:
    """Aggregates player statistics from Silver to Gold layer."""

    def __init__(self, config: LambdaConfig, s3_client: S3Client):
        """
        Initialize the aggregator.

        Args:
            config: Lambda configuration
            s3_client: S3 client for data operations
        """
        self.config = config
        self.s3_client = s3_client

    def process_silver_file(self, bucket: str, key: str) -> dict[str, Any]:
        """
        Process a Silver layer file and create Gold layer aggregations.

        Args:
            bucket: S3 bucket containing the Silver file
            key: S3 key of the Silver file

        Returns:
            Dict with processing statistics
        """
        logger.info(f"Processing Silver file: s3://{bucket}/{key}")

        # Parse season and date from the key
        season, date = self._parse_key_metadata(key)

        # Read Silver layer data
        df = self.s3_client.read_parquet(bucket, key)

        # Validate input data
        validate_input_data(df, self.config)

        # Create daily aggregations
        daily_stats = self._create_daily_aggregations(df, season, date)

        # Get existing season-to-date stats for these players
        season_stats = self._get_season_stats(daily_stats["player_id"].unique(), season)

        # Update season-to-date stats
        updated_season_stats = self._update_season_stats(
            season_stats, daily_stats, date
        )

        # Validate output data
        validate_output_data(daily_stats, self.config)
        validate_output_data(updated_season_stats, self.config)

        # Write Gold layer files
        files_written = self._write_gold_layer_files(
            daily_stats, updated_season_stats, season
        )

        return {
            "players_processed": len(daily_stats),
            "files_written": files_written,
            "season": season,
            "date": date,
        }

    def _parse_key_metadata(self, key: str) -> tuple[str, str]:
        """
        Parse season and date from S3 key.

        Args:
            key: S3 object key

        Returns:
            Tuple of (season, date)
        """
        parts = key.split("/")

        season = None
        date = None

        for part in parts:
            if part.startswith("season="):
                season = part.split("=")[1]
            elif part.startswith("date="):
                date = part.split("=")[1]

        if not season or not date:
            raise ValueError(f"Could not parse season and date from key: {key}")

        return season, date

    def _create_daily_aggregations(
        self, df: pd.DataFrame, season: str, date: str
    ) -> pd.DataFrame:
        """
        Create daily player statistics aggregations.

        Args:
            df: Silver layer DataFrame
            season: Season string (e.g., "2023-24")
            date: Date string (e.g., "2024-01-15")

        Returns:
            DataFrame with daily aggregations
        """
        logger.info(f"Creating daily aggregations for {len(df)} game records")

        # Group by player and aggregate basic stats
        daily_agg = (
            df.groupby("player_id")
            .agg(
                {
                    "points": "sum",
                    "rebounds": "sum",
                    "assists": "sum",
                    "field_goals_made": "sum",
                    "field_goals_attempted": "sum",
                    "three_pointers_made": "sum",
                    "three_pointers_attempted": "sum",
                    "free_throws_made": "sum",
                    "free_throws_attempted": "sum",
                    "steals": "sum",
                    "blocks": "sum",
                    "turnovers": "sum",
                    "minutes_played": "sum",
                }
            )
            .reset_index()
        )
        
        # Add games played count (number of games per player)
        games_count = df.groupby("player_id").size().reset_index(name="games_played")
        daily_agg = daily_agg.merge(games_count, on="player_id")

        # Calculate shooting percentages
        daily_agg["field_goal_percentage"] = np.where(
            daily_agg["field_goals_attempted"] > 0,
            daily_agg["field_goals_made"] / daily_agg["field_goals_attempted"],
            0.0,
        )

        daily_agg["three_point_percentage"] = np.where(
            daily_agg["three_pointers_attempted"] > 0,
            daily_agg["three_pointers_made"] / daily_agg["three_pointers_attempted"],
            0.0,
        )

        daily_agg["free_throw_percentage"] = np.where(
            daily_agg["free_throws_attempted"] > 0,
            daily_agg["free_throws_made"] / daily_agg["free_throws_attempted"],
            0.0,
        )

        # Add metadata
        daily_agg["season"] = season
        daily_agg["date"] = date
        daily_agg["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Created daily aggregations for {len(daily_agg)} players")
        return daily_agg

    def _get_season_stats(self, player_ids: list[str], season: str) -> pd.DataFrame:
        """
        Get existing season-to-date statistics for players.

        Args:
            player_ids: List of player IDs
            season: Season string

        Returns:
            DataFrame with existing season stats (empty if none exist)
        """
        logger.info(
            f"Fetching season stats for {len(player_ids)} players in season {season}"
        )

        season_stats_list = []

        for player_id in player_ids:
            key = (
                f"gold/player_season_stats/season={season}/"
                f"player_id={player_id}/season_stats.parquet"
            )

            try:
                if self.s3_client.object_exists(self.config.gold_bucket, key):
                    player_stats = self.s3_client.read_parquet(
                        self.config.gold_bucket, key
                    )
                    season_stats_list.append(player_stats)
            except Exception as e:
                logger.warning(
                    f"Could not read existing season stats for player {player_id}: {e}"
                )
                # Continue without existing stats - will create new ones

        if season_stats_list:
            season_stats = pd.concat(season_stats_list, ignore_index=True)
            logger.info(f"Found existing season stats for {len(season_stats)} players")
        else:
            # Create empty DataFrame with expected schema
            season_stats = pd.DataFrame(
                columns=[
                    "player_id",
                    "season",
                    "games_played",
                    "points",
                    "rebounds",
                    "assists",
                    "field_goals_made",
                    "field_goals_attempted",
                    "field_goal_percentage",
                    "three_pointers_made",
                    "three_pointers_attempted",
                    "three_point_percentage",
                    "free_throws_made",
                    "free_throws_attempted",
                    "free_throw_percentage",
                    "steals",
                    "blocks",
                    "turnovers",
                    "minutes_played",
                    "updated_at",
                ]
            )
            logger.info("No existing season stats found, will create new records")

        return season_stats

    def _update_season_stats(
        self, season_stats: pd.DataFrame, daily_stats: pd.DataFrame, date: str
    ) -> pd.DataFrame:
        """
        Update season-to-date statistics with new daily stats.

        Args:
            season_stats: Existing season statistics
            daily_stats: New daily statistics
            date: Date string for the daily stats

        Returns:
            Updated season statistics DataFrame
        """
        logger.info(f"Updating season stats with daily stats from {date}")

        # For players with existing season stats, add daily stats
        updated_stats = []

        for _, daily_row in daily_stats.iterrows():
            player_id = daily_row["player_id"]

            # Find existing season stats for this player
            existing = season_stats[season_stats["player_id"] == player_id]

            if len(existing) > 0:
                # Update existing stats
                existing_row = existing.iloc[0].copy()

                # Add cumulative stats
                existing_row["games_played"] += daily_row["games_played"]
                existing_row["points"] += daily_row["points"]
                existing_row["rebounds"] += daily_row["rebounds"]
                existing_row["assists"] += daily_row["assists"]
                existing_row["field_goals_made"] += daily_row["field_goals_made"]
                existing_row["field_goals_attempted"] += daily_row[
                    "field_goals_attempted"
                ]
                existing_row["three_pointers_made"] += daily_row["three_pointers_made"]
                existing_row["three_pointers_attempted"] += daily_row[
                    "three_pointers_attempted"
                ]
                existing_row["free_throws_made"] += daily_row["free_throws_made"]
                existing_row["free_throws_attempted"] += daily_row[
                    "free_throws_attempted"
                ]
                existing_row["steals"] += daily_row["steals"]
                existing_row["blocks"] += daily_row["blocks"]
                existing_row["turnovers"] += daily_row["turnovers"]
                existing_row["minutes_played"] += daily_row["minutes_played"]

                # Recalculate percentages
                existing_row["field_goal_percentage"] = (
                    existing_row["field_goals_made"]
                    / existing_row["field_goals_attempted"]
                    if existing_row["field_goals_attempted"] > 0
                    else 0.0
                )
                existing_row["three_point_percentage"] = (
                    existing_row["three_pointers_made"]
                    / existing_row["three_pointers_attempted"]
                    if existing_row["three_pointers_attempted"] > 0
                    else 0.0
                )
                existing_row["free_throw_percentage"] = (
                    existing_row["free_throws_made"]
                    / existing_row["free_throws_attempted"]
                    if existing_row["free_throws_attempted"] > 0
                    else 0.0
                )

                existing_row["updated_at"] = datetime.utcnow().isoformat()
                updated_stats.append(existing_row)

            else:
                # Create new season stats from daily stats
                new_season_row = daily_row.copy()
                # Remove daily-specific fields
                new_season_row = new_season_row.drop(["date"])
                updated_stats.append(new_season_row)

        updated_season_stats = pd.DataFrame(updated_stats)
        logger.info(f"Updated season stats for {len(updated_season_stats)} players")

        return updated_season_stats

    def _write_gold_layer_files(
        self, daily_stats: pd.DataFrame, season_stats: pd.DataFrame, season: str
    ) -> int:
        """
        Write Gold layer files to S3.

        Args:
            daily_stats: Daily statistics DataFrame
            season_stats: Season statistics DataFrame
            season: Season string

        Returns:
            Number of files written
        """
        files_written = 0

        # Write daily stats files (one per player)
        for _, row in daily_stats.iterrows():
            player_id = row["player_id"]
            date = row["date"]

            # Create single-row DataFrame for this player
            player_daily = pd.DataFrame([row])

            # Write daily stats
            daily_key = (
                f"gold/player_daily_stats/season={season}/"
                f"player_id={player_id}/date={date}/daily_stats.parquet"
            )
            self.s3_client.write_parquet(
                player_daily, self.config.gold_bucket, daily_key
            )
            files_written += 1

        # Write season stats files (one per player)
        for _, row in season_stats.iterrows():
            player_id = row["player_id"]

            # Create single-row DataFrame for this player
            player_season = pd.DataFrame([row])

            # Write season stats
            season_key = (
                f"gold/player_season_stats/season={season}/"
                f"player_id={player_id}/season_stats.parquet"
            )
            self.s3_client.write_parquet(
                player_season, self.config.gold_bucket, season_key
            )
            files_written += 1

        logger.info(f"Wrote {files_written} Gold layer files to S3")
        return files_written
