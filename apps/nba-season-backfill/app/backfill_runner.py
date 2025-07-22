"""
Main backfill runner that orchestrates the NBA season data collection.

Coordinates NBA API client, S3 storage, and state management to execute
the complete backfill process with proper error handling and observability.
"""

import time
from datetime import datetime
from typing import Any

from hoopstat_observability import get_logger

from .config import BackfillConfig
from .nba_client import NBAClient
from .s3_client import S3Client
from .state_manager import BackfillState

logger = get_logger(__name__)


class BackfillRunner:
    """
    Main orchestrator for NBA season backfill operation.

    Coordinates all components to execute backfill with proper
    error handling, state management, and observability.
    """

    def __init__(self, config: BackfillConfig):
        """
        Initialize backfill runner.

        Args:
            config: Backfill configuration
        """
        self.config = config
        self.state: BackfillState | None = None
        self.nba_client: NBAClient | None = None
        self.s3_client: S3Client | None = None

        logger.info(
            "Backfill runner initialized",
            season=config.target_season,
            dry_run=config.dry_run,
            resume=config.resume_from_checkpoint,
        )

    def _initialize_clients(self) -> None:
        """Initialize NBA API and S3 clients."""
        logger.info("Initializing clients")

        # Initialize NBA API client
        self.nba_client = NBAClient(
            rate_limit_seconds=self.config.rate_limit_seconds,
            max_retries=self.config.max_retries,
        )

        # Initialize S3 client (skip in dry run mode)
        if not self.config.dry_run:
            self.s3_client = S3Client(
                bucket=self.config.s3_bucket,
                region=self.config.aws_region,
            )

        logger.info("Clients initialized successfully")

    def _load_or_create_state(self) -> None:
        """Load existing state or create new state."""
        if self.config.resume_from_checkpoint:
            logger.info("Attempting to resume from checkpoint")

            if self.s3_client:
                existing_state = self.s3_client.download_state_file(
                    self.config.state_file_path
                )

                if existing_state:
                    self.state = BackfillState.from_dict(existing_state)
                    logger.info(
                        "Resumed from existing checkpoint",
                        backfill_id=self.state.backfill_id,
                        completed_games=len(self.state.completed_games),
                    )
                else:
                    logger.warning("No checkpoint found, starting fresh")
                    self.state = BackfillState()
            else:
                logger.warning("Cannot resume in dry run mode, starting fresh")
                self.state = BackfillState()
        else:
            logger.info("Starting fresh backfill")
            self.state = BackfillState()

        # Store config snapshot
        self.state.set_config_snapshot(self.config.dict())
        self.state.set_current_season(self.config.target_season)

    def _save_checkpoint(self) -> None:
        """Save current state as checkpoint."""
        if self.config.dry_run or not self.s3_client or not self.state:
            return

        try:
            self.state.update_checkpoint()
            state_data = self.state.to_dict()

            self.s3_client.upload_state_file(
                state_data,
                self.config.state_file_path,
                dry_run=self.config.dry_run,
            )

        except Exception as e:
            logger.error(
                "Failed to save checkpoint",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Don't fail the entire operation for checkpoint save failure

    def _process_game(self, game_info: list[Any]) -> bool:
        """
        Process a single game and collect all requested data types.

        Args:
            game_info: Game information from NBA API

        Returns:
            True if successful, False if failed
        """
        # Extract game details
        game_id = str(game_info[2])  # GAME_ID is at index 2
        game_date = str(game_info[5])  # GAME_DATE is at index 5

        # Parse and format game date
        try:
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(
                "Invalid game date format",
                game_id=game_id,
                game_date=game_date,
            )
            formatted_date = game_date

        logger.info(
            "Processing game",
            game_id=game_id,
            game_date=formatted_date,
            season=self.config.target_season,
        )

        files_uploaded = 0
        bytes_stored = 0
        api_calls = 0

        try:
            # Collect box scores
            if self.config.collect_box_scores:
                # Traditional box score
                start_time = time.time()
                if not self.config.dry_run:
                    box_score_data = self.nba_client.get_box_score_traditional(game_id)
                    api_calls += 1

                    # Extract player stats (usually in resultSets[0])
                    player_stats = []
                    if (
                        "resultSets" in box_score_data
                        and len(box_score_data["resultSets"]) > 0
                    ):
                        headers = box_score_data["resultSets"][0]["headers"]
                        rows = box_score_data["resultSets"][0]["rowSet"]
                        player_stats = [
                            dict(zip(headers, row, strict=False)) for row in rows
                        ]

                    response_time = time.time() - start_time

                    self.s3_client.upload_game_data(
                        data=player_stats,
                        data_type="box-scores-traditional",
                        game_id=game_id,
                        season=self.config.target_season,
                        game_date=formatted_date,
                        api_response_time=response_time,
                        prefix=self.config.s3_prefix,
                        dry_run=self.config.dry_run,
                    )
                    files_uploaded += 1
                    bytes_stored += len(str(player_stats))
                else:
                    logger.info(
                        "Dry run: would collect traditional box score", game_id=game_id
                    )

                # Advanced box score
                start_time = time.time()
                if not self.config.dry_run:
                    advanced_data = self.nba_client.get_box_score_advanced(game_id)
                    api_calls += 1

                    # Extract advanced stats
                    advanced_stats = []
                    if (
                        "resultSets" in advanced_data
                        and len(advanced_data["resultSets"]) > 0
                    ):
                        headers = advanced_data["resultSets"][0]["headers"]
                        rows = advanced_data["resultSets"][0]["rowSet"]
                        advanced_stats = [
                            dict(zip(headers, row, strict=False)) for row in rows
                        ]

                    response_time = time.time() - start_time

                    self.s3_client.upload_game_data(
                        data=advanced_stats,
                        data_type="box-scores-advanced",
                        game_id=game_id,
                        season=self.config.target_season,
                        game_date=formatted_date,
                        api_response_time=response_time,
                        prefix=self.config.s3_prefix,
                        dry_run=self.config.dry_run,
                    )
                    files_uploaded += 1
                    bytes_stored += len(str(advanced_stats))
                else:
                    logger.info(
                        "Dry run: would collect advanced box score", game_id=game_id
                    )

            # Collect play-by-play
            if self.config.collect_play_by_play:
                start_time = time.time()
                if not self.config.dry_run:
                    pbp_data = self.nba_client.get_play_by_play(game_id)
                    api_calls += 1

                    # Extract play-by-play events
                    play_events = []
                    if "resultSets" in pbp_data and len(pbp_data["resultSets"]) > 0:
                        headers = pbp_data["resultSets"][0]["headers"]
                        rows = pbp_data["resultSets"][0]["rowSet"]
                        play_events = [
                            dict(zip(headers, row, strict=False)) for row in rows
                        ]

                    response_time = time.time() - start_time

                    self.s3_client.upload_game_data(
                        data=play_events,
                        data_type="play-by-play",
                        game_id=game_id,
                        season=self.config.target_season,
                        game_date=formatted_date,
                        api_response_time=response_time,
                        prefix=self.config.s3_prefix,
                        dry_run=self.config.dry_run,
                    )
                    files_uploaded += 1
                    bytes_stored += len(str(play_events))
                else:
                    logger.info("Dry run: would collect play-by-play", game_id=game_id)

            # Mark game as completed
            self.state.mark_game_completed(
                game_id=game_id,
                files_uploaded=files_uploaded,
                bytes_stored=bytes_stored,
                api_calls=api_calls,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to process game",
                game_id=game_id,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Mark game as failed
            retry_count = self.state.get_failed_game_retry_count(game_id)
            self.state.mark_game_failed(
                game_id=game_id,
                error_message=str(e),
                error_type=type(e).__name__,
                retry_count=retry_count + 1,
            )

            return False

    def run(self) -> dict[str, Any]:
        """
        Execute the complete backfill operation.

        Returns:
            Summary of backfill results
        """
        try:
            # Initialize components
            self._initialize_clients()
            self._load_or_create_state()

            logger.info(
                "Starting backfill execution",
                season=self.config.target_season,
                backfill_id=self.state.backfill_id,
            )

            # Get season games
            if not self.config.dry_run:
                games = self.nba_client.get_season_games(self.config.target_season)
            else:
                # Mock games for dry run
                games = [
                    [None, None, f"mock_game_{i}", None, None, "2024-10-15"]
                    for i in range(5)
                ]

            total_games = len(games)

            logger.info(
                "Season games discovered",
                total_games=total_games,
                season=self.config.target_season,
            )

            # Process games
            processed_count = 0
            for _i, game_info in enumerate(games):
                game_id = str(game_info[2])

                # Skip if already completed
                if self.state.is_game_completed(game_id):
                    logger.debug("Skipping already completed game", game_id=game_id)
                    continue

                # Check if this is a failed game that should be retried
                if self.state.is_game_failed(game_id):
                    retry_count = self.state.get_failed_game_retry_count(game_id)
                    if retry_count >= self.config.max_retries:
                        logger.info(
                            "Skipping game - max retries exceeded",
                            game_id=game_id,
                            retry_count=retry_count,
                        )
                        continue

                # Process the game
                self._process_game(game_info)
                processed_count += 1

                # Save checkpoint periodically
                if processed_count % self.config.checkpoint_frequency == 0:
                    self._save_checkpoint()

                    progress = self.state.get_progress_summary(total_games)
                    logger.info(
                        "Checkpoint saved - progress update",
                        **progress["progress"],
                    )

            # Final checkpoint
            self._save_checkpoint()

            # Generate final summary
            final_progress = self.state.get_progress_summary(total_games)

            # Get API client statistics
            api_stats = {}
            if self.nba_client:
                api_stats = self.nba_client.get_session_stats()

            result = {
                **final_progress,
                "api_statistics": api_stats,
                "completion_status": "success",
            }

            logger.info(
                "Backfill execution completed successfully",
                **result["progress"],
                **api_stats,
            )

            return result

        except Exception as e:
            logger.error(
                "Backfill execution failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            # Try to save final state
            try:
                self._save_checkpoint()
            except Exception:
                logger.error("Failed to save final checkpoint")

            # Return failure summary
            return {
                "completion_status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "progress": self.state.get_progress_summary() if self.state else {},
            }
