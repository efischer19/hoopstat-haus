"""Core bronze layer ingestion logic."""

import time

import pandas as pd
from hoopstat_observability import get_logger, performance_context

from .config import BronzeIngestionConfig
from .nba_client import NBAAPIClient
from .s3_client import S3ParquetClient

logger = get_logger(__name__)


class BronzeIngester:
    """Core bronze layer ingestion orchestrator."""

    def __init__(self, config: BronzeIngestionConfig):
        """Initialize the ingester.

        Args:
            config: Configuration object
        """
        self.config = config
        self.nba_client = NBAAPIClient(config)
        self.s3_client = S3ParquetClient(config)

    def ingest_for_date(self, game_date: str, dry_run: bool = False) -> dict[str, int]:
        """Ingest NBA data for a specific date.

        Args:
            game_date: Date in YYYY-MM-DD format
            dry_run: If True, fetch data but don't write to S3

        Returns:
            Dictionary with counts of records processed by entity type

        Raises:
            ValueError: If ingestion fails
        """
        start_time = time.time()

        with performance_context(
            "bronze_ingestion", {"game_date": game_date, "dry_run": dry_run}
        ):
            logger.info(f"Starting bronze ingestion for date: {game_date}")

            # Step 1: Fetch schedule to check if games exist
            try:
                schedule_df = self.nba_client.get_schedule_for_date(game_date)
            except Exception as e:
                logger.error(f"Failed to fetch schedule for {game_date}: {e}")
                raise ValueError(f"Schedule fetch failed: {e}") from e

            # Step 2: Check if any games exist for the date
            if schedule_df.empty:
                logger.info(f"No games found for {game_date}, exiting successfully")
                return {"schedule": 0, "box_score": 0, "play_by_play": 0}

            # Extract unique game IDs from schedule
            game_ids = self._extract_game_ids(schedule_df)
            logger.info(f"Found {len(game_ids)} games for {game_date}: {game_ids}")

            records_processed = {}

            # Step 3: Process schedule data
            records_processed["schedule"] = len(schedule_df)
            if not dry_run:
                self.s3_client.write_parquet(schedule_df, "schedule", game_date)
                logger.info(f"Wrote schedule data: {len(schedule_df)} records")

            # Step 4: Process each game's detailed data
            all_box_scores = []
            all_play_by_play = []

            for game_id in game_ids:
                try:
                    # Fetch box score
                    box_score_df = self.nba_client.get_box_score(game_id)
                    if not box_score_df.empty:
                        # Add game_date column for partitioning
                        box_score_df["game_date"] = game_date
                        all_box_scores.append(box_score_df)

                    # Fetch play-by-play
                    play_by_play_df = self.nba_client.get_play_by_play(game_id)
                    if not play_by_play_df.empty:
                        # Add game_date column for partitioning
                        play_by_play_df["game_date"] = game_date
                        all_play_by_play.append(play_by_play_df)

                except Exception as e:
                    logger.error(f"Failed to fetch data for game {game_id}: {e}")
                    # Continue with other games rather than failing completely
                    continue

            # Step 5: Combine and write box score data
            if all_box_scores:
                combined_box_scores = pd.concat(all_box_scores, ignore_index=True)
                records_processed["box_score"] = len(combined_box_scores)
                if not dry_run:
                    self.s3_client.write_parquet(
                        combined_box_scores, "box_score", game_date
                    )
                    logger.info(
                        f"Wrote box score data: {len(combined_box_scores)} records"
                    )
            else:
                records_processed["box_score"] = 0
                logger.warning(f"No box score data found for {game_date}")

            # Step 6: Combine and write play-by-play data
            if all_play_by_play:
                combined_play_by_play = pd.concat(all_play_by_play, ignore_index=True)
                records_processed["play_by_play"] = len(combined_play_by_play)
                if not dry_run:
                    self.s3_client.write_parquet(
                        combined_play_by_play, "play_by_play", game_date
                    )
                    logger.info(
                        f"Wrote play-by-play data: {len(combined_play_by_play)} records"
                    )
            else:
                records_processed["play_by_play"] = 0
                logger.warning(f"No play-by-play data found for {game_date}")

            # Step 7: Log completion with performance metrics
            duration = time.time() - start_time
            total_records = sum(records_processed.values())

            logger.info(
                "Bronze ingestion completed successfully",
                extra={
                    "game_date": game_date,
                    "duration_in_seconds": round(duration, 2),
                    "records_processed": total_records,
                    "games_processed": len(game_ids),
                    "dry_run": dry_run,
                    "entity_counts": records_processed,
                },
            )

            return records_processed

    def _extract_game_ids(self, schedule_df: pd.DataFrame) -> list[str]:
        """Extract unique game IDs from schedule DataFrame.

        Args:
            schedule_df: Schedule data from NBA API

        Returns:
            List of unique game IDs
        """
        if "GAME_ID" in schedule_df.columns:
            return schedule_df["GAME_ID"].unique().tolist()

        # If GAME_ID column doesn't exist, log the available columns for debugging
        logger.warning(
            f"GAME_ID column not found. Available columns: "
            f"{schedule_df.columns.tolist()}"
        )

        # Try alternative column names that might contain game IDs
        possible_id_columns = ["game_id", "gameId", "id", "Game_ID"]
        for col in possible_id_columns:
            if col in schedule_df.columns:
                logger.info(f"Using {col} column for game IDs")
                return schedule_df[col].unique().tolist()

        # If no game ID column found, return empty list
        logger.error("No game ID column found in schedule data")
        return []

    def check_existing_data(self, game_date: str) -> dict[str, bool]:
        """Check what data already exists for a given date.

        Args:
            game_date: Date in YYYY-MM-DD format

        Returns:
            Dictionary indicating which entities have existing data
        """
        entities = ["schedule", "box_score", "play_by_play"]
        existing_data = {}

        for entity in entities:
            existing_data[entity] = self.s3_client.file_exists(entity, game_date)

        return existing_data
