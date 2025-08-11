"""
Date-scoped ingestion logic for bronze layer.
"""

from datetime import date
from typing import Any

import pandas as pd
from hoopstat_nba_api import NBAClient
from hoopstat_observability import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import BronzeIngestionConfig
from .s3_manager import BronzeS3Manager

logger = get_logger(__name__)


class DateScopedIngestion:
    """Date-scoped NBA data ingestion for bronze layer."""

    def __init__(self, config: BronzeIngestionConfig | None = None):
        """Initialize the ingestion system."""
        self.config = config or BronzeIngestionConfig.load()
        self.nba_client = NBAClient()
        self.s3_manager = BronzeS3Manager(
            bucket_name=self.config.bronze_bucket, region_name=self.config.aws_region
        )

    def run(self, target_date: date, dry_run: bool = False) -> bool:
        """
        Run the date-scoped ingestion process.

        Args:
            target_date: Date to fetch data for
            dry_run: If True, don't write data to S3

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting ingestion for {target_date}")

            # Step 1: Fetch schedule for the date
            games = self._fetch_schedule(target_date)

            # Step 2: Early exit if no games for this date
            if not games:
                logger.info(f"No games found for {target_date}, exiting successfully")
                return True

            logger.info(f"Found {len(games)} games for {target_date}")

            # Step 3: Store schedule as Parquet
            if not dry_run:
                self._store_schedule(games, target_date)
            else:
                logger.info("Dry run: would store schedule data")

            # Step 4: Fetch and store box scores for each game
            for game in games:
                game_id = str(game.get("GAME_ID", ""))
                if game_id:
                    box_score = self._fetch_box_score(game_id)
                    if box_score and not dry_run:
                        self._store_box_score(box_score, game_id, target_date)
                    elif box_score:
                        logger.info(
                            f"Dry run: would store box score for game {game_id}"
                        )

            logger.info(f"Ingestion completed for {target_date}")
            return True

        except Exception as e:
            logger.error(f"Ingestion failed for {target_date}: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _fetch_schedule(self, target_date: date) -> list[dict[str, Any]]:
        """Fetch games schedule for the target date."""
        try:
            logger.info(f"Fetching schedule for {target_date}")
            games = self.nba_client.get_games_for_date(target_date)
            logger.info(f"Successfully fetched {len(games)} games")
            return games
        except Exception as e:
            logger.error(f"Failed to fetch schedule for {target_date}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _fetch_box_score(self, game_id: str) -> dict[str, Any] | None:
        """Fetch box score for a specific game."""
        try:
            logger.debug(f"Fetching box score for game {game_id}")
            box_score = self.nba_client.get_box_score(game_id)
            logger.debug(f"Successfully fetched box score for game {game_id}")
            return box_score
        except Exception as e:
            logger.warning(f"Failed to fetch box score for game {game_id}: {e}")
            return None

    def _store_schedule(self, games: list[dict[str, Any]], target_date: date) -> None:
        """Store schedule data as Parquet in S3."""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(games)

            # Store as Parquet
            self.s3_manager.store_parquet(
                df, entity="schedule", target_date=target_date
            )
            logger.info(f"Stored schedule data for {target_date}")

        except Exception as e:
            logger.error(f"Failed to store schedule data: {e}")
            raise

    def _store_box_score(
        self, box_score: dict[str, Any], game_id: str, target_date: date
    ) -> None:
        """Store box score data as Parquet in S3."""
        try:
            # Flatten the nested box score structure for Parquet storage
            flattened_data = self._flatten_box_score(box_score)

            # Convert to DataFrame
            df = pd.DataFrame([flattened_data])

            # Store as Parquet with game_id in the key
            self.s3_manager.store_parquet(
                df,
                entity="box_scores",
                target_date=target_date,
                partition_suffix=f"/{game_id}",
            )
            logger.debug(f"Stored box score for game {game_id}")

        except Exception as e:
            logger.error(f"Failed to store box score for game {game_id}: {e}")
            raise

    def _flatten_box_score(self, box_score: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested box score structure for Parquet storage."""
        flattened = {
            "game_id": box_score.get("game_id"),
            "fetch_date": box_score.get("fetch_date"),
        }

        # Extract key statistics from nested structure
        # This is a simplified flattening - in production would need more
        # sophisticated handling
        if "resultSets" in box_score:
            result_sets = box_score["resultSets"]
            if result_sets and len(result_sets) > 0:
                first_result = result_sets[0]
                if "rowSet" in first_result and first_result["rowSet"]:
                    # Add summary stats from first row of first result set
                    flattened["result_set_name"] = first_result.get("name", "")
                    flattened["row_count"] = len(first_result["rowSet"])

        return flattened
