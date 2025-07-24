"""Core backfill runner for NBA season data collection."""

import logging
import time
from datetime import datetime

from .config import BackfillConfig
from .nba_client import NBAClient
from .state_manager import StateManager
from .storage_client import S3StorageClient


class BackfillRunner:
    """Main orchestrator for NBA season data backfill."""

    def __init__(self, config: BackfillConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self.nba_client = NBAClient(config)
        self.storage_client = S3StorageClient(config)
        self.state_manager = StateManager(config)

        # Operation tracking
        self.start_time = datetime.now()
        self.is_resuming = False

    def run(self) -> bool:
        """Execute the backfill operation."""
        try:
            self.logger.info(
                "Starting NBA season backfill",
                extra={
                    "season": self.config.season,
                    "dry_run": self.config.dry_run,
                    "rate_limit_seconds": self.config.rate_limit_seconds,
                },
            )

            # Attempt to resume from existing state
            if not self._try_resume_from_checkpoint():
                # Fresh start - discover games
                if not self._discover_season_games():
                    return False

            # Process games
            success = self._process_games()

            # Final summary
            self._log_final_summary()

            return success

        except KeyboardInterrupt:
            self.logger.info("Backfill interrupted by user")
            self._save_checkpoint()
            return False
        except Exception as e:
            self.logger.error(f"Backfill failed with error: {e}", exc_info=True)
            self._save_checkpoint()
            return False

    def _try_resume_from_checkpoint(self) -> bool:
        """Try to resume from an existing checkpoint."""
        state_data = self.storage_client.load_state_file()

        if state_data is None:
            self.logger.info("No existing checkpoint found, starting fresh")
            return False

        if self.state_manager.load_existing_state(state_data):
            self.is_resuming = True

            # Validate state integrity
            issues = self.state_manager.validate_state_integrity()
            if issues:
                self.logger.warning(f"State integrity issues found: {issues}")

            self.logger.info(
                "Resuming from checkpoint",
                extra=self.state_manager.get_progress_summary(),
            )
            return True

        return False

    def _discover_season_games(self) -> bool:
        """Discover all games for the season."""
        try:
            self.logger.info(f"Discovering games for season {self.config.season}")

            response = self.nba_client.get_season_games(self.config.season)

            if not response.data:
                self.logger.error("No data returned from NBA API for season games")
                return False

            # Assuming the first DataFrame contains game information
            games_df = response.data[0]

            if games_df.empty:
                self.logger.error(f"No games found for season {self.config.season}")
                return False

            # Convert DataFrame to list of dicts for state manager
            games_list = games_df.to_dict("records")
            self.state_manager.add_discovered_games(games_list)

            self.logger.info(
                f"Discovered {len(games_list)} games for season {self.config.season}",
                extra={"total_games": len(games_list), "season": self.config.season},
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to discover season games: {e}", exc_info=True)
            return False

    def _process_games(self) -> bool:
        """Process all pending games."""
        total_processed = 0
        consecutive_failures = 0
        max_consecutive_failures = 10

        while True:
            # Get next batch of games to process
            games_to_process = self.state_manager.get_next_games_to_process(
                batch_size=1
            )

            if not games_to_process:
                self.logger.info("All games processed")
                break

            game = games_to_process[0]

            try:
                success = self._process_single_game(game.game_id, game.game_date)

                if success:
                    consecutive_failures = 0
                    total_processed += 1

                    if total_processed % 10 == 0:
                        self.logger.info(
                            "Progress update",
                            extra=self.state_manager.get_progress_summary(),
                        )
                else:
                    consecutive_failures += 1

                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error(
                            f"Too many consecutive failures "
                            f"({consecutive_failures}), stopping"
                        )
                        return False

                # Save checkpoint if needed
                if self.state_manager.should_save_checkpoint():
                    self._save_checkpoint()
                    self.state_manager.reset_checkpoint_counter()

            except Exception as e:
                self.logger.error(
                    f"Unexpected error processing game {game.game_id}: {e}",
                    exc_info=True,
                )
                consecutive_failures += 1

        # Final checkpoint
        self._save_checkpoint()
        return True

    def _process_single_game(self, game_id: str, game_date: str) -> bool:
        """Process data for a single game."""
        game_start_time = time.time()
        api_calls_made = 0
        files_stored = 0
        bytes_stored = 0

        try:
            self.logger.debug(f"Processing game {game_id}")

            # Parse game date
            try:
                parsed_date = datetime.strptime(game_date, "%Y-%m-%d")
            except ValueError:
                # Try alternative format
                parsed_date = datetime.strptime(game_date[:10], "%Y-%m-%d")

            data_types_completed = []

            # Process traditional box scores
            if self._process_game_data_type(
                game_id,
                parsed_date,
                "box-scores-traditional",
                self.nba_client.get_game_box_score_traditional,
            ):
                data_types_completed.append("box-scores-traditional")
                api_calls_made += 1
                files_stored += 1

            # Process advanced box scores
            if self._process_game_data_type(
                game_id,
                parsed_date,
                "box-scores-advanced",
                self.nba_client.get_game_box_score_advanced,
            ):
                data_types_completed.append("box-scores-advanced")
                api_calls_made += 1
                files_stored += 1

            # Process play-by-play data
            if self._process_game_data_type(
                game_id,
                parsed_date,
                "play-by-play",
                self.nba_client.get_game_play_by_play,
            ):
                data_types_completed.append("play-by-play")
                api_calls_made += 1
                files_stored += 1

            # Mark as completed if we got at least some data
            if data_types_completed:
                self.state_manager.mark_game_completed(game_id, data_types_completed)

                processing_time = time.time() - game_start_time

                self.logger.info(
                    "Game processed successfully",
                    extra={
                        "game_id": game_id,
                        "data_types_completed": data_types_completed,
                        "processing_time_seconds": round(processing_time, 2),
                        "api_calls": api_calls_made,
                    },
                )

                # Update statistics
                storage_stats = self.storage_client.get_storage_stats()
                bytes_stored = storage_stats.get("total_bytes_uploaded", 0)
                self.state_manager.update_api_stats(
                    api_calls_made, files_stored, bytes_stored
                )

                return True
            else:
                error_msg = f"No data collected for game {game_id}"
                self.state_manager.mark_game_failed(game_id, error_msg)
                self.logger.error(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error processing game {game_id}: {str(e)}"
            self.state_manager.mark_game_failed(game_id, error_msg)
            self.logger.error(error_msg, exc_info=True)
            return False

    def _process_game_data_type(
        self, game_id: str, game_date: datetime, data_type: str, api_method
    ) -> bool:
        """Process a specific data type for a game."""
        try:
            # Get data from NBA API
            response = api_method(game_id)

            if response.error:
                self.logger.warning(
                    f"API error for {data_type} game {game_id}: {response.error}"
                )
                return False

            if not response.data or all(df.empty for df in response.data):
                self.logger.warning(
                    f"Empty data returned for {data_type} game {game_id}"
                )
                return False

            # Store in S3
            api_metadata = {
                "endpoint": response.endpoint,
                "api_response_time_ms": response.response_time_ms,
                "game_id": game_id,
            }

            success = self.storage_client.store_game_data(
                data_type=data_type,
                game_id=game_id,
                season=self.config.season,
                game_date=game_date,
                dataframes=response.data,
                api_metadata=api_metadata,
            )

            if not success:
                self.logger.error(
                    f"Failed to store {data_type} data for game {game_id}"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(
                f"Error processing {data_type} for game {game_id}: {e}", exc_info=True
            )
            return False

    def _save_checkpoint(self) -> None:
        """Save current state as checkpoint."""
        try:
            state_data = self.state_manager.to_dict()

            if self.storage_client.store_state_file(state_data):
                self.logger.info("Checkpoint saved successfully")
            else:
                self.logger.error("Failed to save checkpoint")

        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}", exc_info=True)

    def _log_final_summary(self) -> None:
        """Log final summary of the backfill operation."""
        total_time = datetime.now() - self.start_time
        progress = self.state_manager.get_progress_summary()
        api_stats = self.nba_client.get_stats_summary()
        storage_stats = self.storage_client.get_storage_stats()

        self.logger.info(
            "Backfill operation completed",
            extra={
                "duration_in_seconds": total_time.total_seconds(),
                "records_processed": progress["completed_games"],
                "total_runtime_hours": round(total_time.total_seconds() / 3600, 2),
                "games_completed": progress["completed_games"],
                "games_failed": progress["failed_games"],
                "completion_percentage": progress["completion_percentage"],
                "api_calls_made": api_stats["total_requests"],
                "api_success_rate": api_stats["success_rate"],
                "files_uploaded": storage_stats["files_uploaded"],
                "total_bytes_uploaded": storage_stats["total_bytes_uploaded"],
                "was_resumed": self.is_resuming,
            },
        )

        # Log failed games if any
        failed_games = self.state_manager.get_failed_games_summary()
        if failed_games:
            self.logger.warning(
                f"Failed games summary: {len(failed_games)} games failed",
                extra={"failed_games": failed_games[:10]},  # Log first 10
            )
