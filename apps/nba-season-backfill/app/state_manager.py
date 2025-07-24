"""State management for resumable backfill operations."""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .config import BackfillConfig


@dataclass
class GameProcessingState:
    """State information for a single game."""

    game_id: str
    game_date: str
    status: str  # "pending", "completed", "failed"
    retry_count: int = 0
    last_attempt: str | None = None
    error_message: str | None = None
    data_types_completed: list[str] = None

    def __post_init__(self):
        if self.data_types_completed is None:
            self.data_types_completed = []


@dataclass
class BackfillStats:
    """Statistics for the backfill operation."""

    start_time: str
    last_update: str
    total_games_discovered: int = 0
    games_completed: int = 0
    games_failed: int = 0
    games_pending: int = 0
    total_api_calls: int = 0
    total_files_stored: int = 0
    total_bytes_stored: int = 0
    average_processing_rate: float = 0.0  # games per hour
    estimated_completion: str | None = None


class StateManager:
    """Manages checkpoint state for resumable backfill operations."""

    def __init__(self, config: BackfillConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize state
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.backfill_id = f"{timestamp}-season-{config.season}-backfill"
        self.games: dict[str, GameProcessingState] = {}
        self.stats = BackfillStats(
            start_time=datetime.now().isoformat(),
            last_update=datetime.now().isoformat(),
        )

        # Track data types to collect
        self.data_types = [
            "games",
            "box-scores-traditional",
            "box-scores-advanced",
            "play-by-play",
        ]

        self.checkpoint_counter = 0

    def load_existing_state(self, state_data: dict[str, Any]) -> bool:
        """Load state from previously saved checkpoint."""
        try:
            # Load basic info
            self.backfill_id = state_data.get("backfill_id", self.backfill_id)

            # Load games state
            games_data = state_data.get("games", {})
            self.games = {
                game_id: GameProcessingState(**game_data)
                for game_id, game_data in games_data.items()
            }

            # Load statistics
            stats_data = state_data.get("stats", {})
            self.stats = BackfillStats(**stats_data)

            # Recalculate pending games count
            self.stats.games_pending = sum(
                1 for game in self.games.values() if game.status == "pending"
            )

            self.logger.info(
                "Loaded existing state",
                extra={
                    "backfill_id": self.backfill_id,
                    "total_games": len(self.games),
                    "completed_games": self.stats.games_completed,
                    "failed_games": self.stats.games_failed,
                    "pending_games": self.stats.games_pending,
                },
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to load existing state: {e}")
            return False

    def add_discovered_games(self, games: list[dict[str, Any]]) -> None:
        """Add newly discovered games to the state."""
        new_games = 0

        for game_data in games:
            game_id = str(game_data.get("GAME_ID", ""))
            game_date = str(game_data.get("GAME_DATE", ""))

            if game_id and game_id not in self.games:
                self.games[game_id] = GameProcessingState(
                    game_id=game_id, game_date=game_date, status="pending"
                )
                new_games += 1

        self.stats.total_games_discovered = len(self.games)
        self.stats.games_pending = sum(
            1 for game in self.games.values() if game.status == "pending"
        )

        self.logger.info(f"Added {new_games} new games to processing queue")

    def mark_game_completed(
        self, game_id: str, data_types_completed: list[str]
    ) -> None:
        """Mark a game as successfully completed."""
        if game_id in self.games:
            game = self.games[game_id]
            previous_status = game.status

            game.status = "completed"
            game.data_types_completed = data_types_completed
            game.last_attempt = datetime.now().isoformat()

            self.stats.games_completed += 1
            if previous_status == "pending":
                self.stats.games_pending = max(0, self.stats.games_pending - 1)
            elif previous_status == "failed":
                self.stats.games_failed = max(0, self.stats.games_failed - 1)

        self._update_processing_rate()

    def mark_game_failed(
        self, game_id: str, error_message: str, increment_retry: bool = True
    ) -> None:
        """Mark a game as failed with error details."""
        if game_id in self.games:
            game = self.games[game_id]
            previous_status = game.status

            if increment_retry:
                game.retry_count += 1

            game.error_message = error_message
            game.last_attempt = datetime.now().isoformat()

            # Check if we should mark as permanently failed
            if game.retry_count >= self.config.max_retries:
                if previous_status != "failed":
                    game.status = "failed"
                    self.stats.games_failed += 1
                    if previous_status == "pending":
                        self.stats.games_pending = max(0, self.stats.games_pending - 1)
            else:
                # Still pending for retry
                game.status = "pending"

    def get_next_games_to_process(
        self, batch_size: int = 1
    ) -> list[GameProcessingState]:
        """Get the next games that need to be processed."""
        pending_games = [
            game for game in self.games.values() if game.status == "pending"
        ]

        # Sort by retry count (process games with fewer retries first)
        pending_games.sort(key=lambda g: g.retry_count)

        return pending_games[:batch_size]

    def should_save_checkpoint(self) -> bool:
        """Determine if it's time to save a checkpoint."""
        self.checkpoint_counter += 1
        return self.checkpoint_counter >= self.config.checkpoint_frequency

    def reset_checkpoint_counter(self) -> None:
        """Reset the checkpoint counter after saving."""
        self.checkpoint_counter = 0

    def update_api_stats(
        self, api_calls: int, files_stored: int, bytes_stored: int
    ) -> None:
        """Update API and storage statistics."""
        self.stats.total_api_calls += api_calls
        self.stats.total_files_stored += files_stored
        self.stats.total_bytes_stored += bytes_stored
        self.stats.last_update = datetime.now().isoformat()

    def _update_processing_rate(self) -> None:
        """Update the processing rate and ETA calculations."""
        try:
            start_time = datetime.fromisoformat(self.stats.start_time)
            current_time = datetime.now()
            elapsed_hours = (current_time - start_time).total_seconds() / 3600

            if elapsed_hours > 0:
                self.stats.average_processing_rate = (
                    self.stats.games_completed / elapsed_hours
                )

                # Calculate ETA
                if (
                    self.stats.average_processing_rate > 0
                    and self.stats.games_pending > 0
                ):
                    hours_remaining = (
                        self.stats.games_pending / self.stats.average_processing_rate
                    )
                    eta = current_time.timestamp() + (hours_remaining * 3600)
                    self.stats.estimated_completion = datetime.fromtimestamp(
                        eta
                    ).isoformat()
                else:
                    self.stats.estimated_completion = None

        except Exception as e:
            self.logger.warning(f"Error updating processing rate: {e}")

    def get_progress_summary(self) -> dict[str, Any]:
        """Get a summary of current progress."""
        total_games = len(self.games)
        completed_percentage = (
            (self.stats.games_completed / total_games * 100) if total_games > 0 else 0
        )

        return {
            "backfill_id": self.backfill_id,
            "season": self.config.season,
            "total_games": total_games,
            "completed_games": self.stats.games_completed,
            "failed_games": self.stats.games_failed,
            "pending_games": self.stats.games_pending,
            "completion_percentage": round(completed_percentage, 2),
            "processing_rate_per_hour": round(self.stats.average_processing_rate, 2),
            "estimated_completion": self.stats.estimated_completion,
            "total_api_calls": self.stats.total_api_calls,
            "total_files_stored": self.stats.total_files_stored,
            "total_bytes_stored": self.stats.total_bytes_stored,
            "last_update": self.stats.last_update,
        }

    def get_failed_games_summary(self) -> list[dict[str, Any]]:
        """Get summary of failed games for troubleshooting."""
        failed_games = [
            {
                "game_id": game.game_id,
                "game_date": game.game_date,
                "retry_count": game.retry_count,
                "error_message": game.error_message,
                "last_attempt": game.last_attempt,
            }
            for game in self.games.values()
            if game.status == "failed"
        ]

        return failed_games

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "backfill_id": self.backfill_id,
            "season": self.config.season,
            "data_types": self.data_types,
            "games": {game_id: asdict(game) for game_id, game in self.games.items()},
            "stats": asdict(self.stats),
            "checkpoint_metadata": {
                "last_checkpoint": datetime.now().isoformat(),
                "config_snapshot": {
                    "rate_limit_seconds": self.config.rate_limit_seconds,
                    "max_retries": self.config.max_retries,
                    "checkpoint_frequency": self.config.checkpoint_frequency,
                },
            },
        }

    def validate_state_integrity(self) -> list[str]:
        """Validate state integrity and return any issues found."""
        issues = []

        # Check statistics consistency
        calculated_completed = sum(
            1 for g in self.games.values() if g.status == "completed"
        )
        if calculated_completed != self.stats.games_completed:
            issues.append(
                f"Completed games count mismatch: {calculated_completed} vs "
                f"{self.stats.games_completed}"
            )

        calculated_failed = sum(1 for g in self.games.values() if g.status == "failed")
        if calculated_failed != self.stats.games_failed:
            issues.append(
                f"Failed games count mismatch: {calculated_failed} vs "
                f"{self.stats.games_failed}"
            )

        calculated_pending = sum(
            1 for g in self.games.values() if g.status == "pending"
        )
        if calculated_pending != self.stats.games_pending:
            issues.append(
                f"Pending games count mismatch: {calculated_pending} vs "
                f"{self.stats.games_pending}"
            )

        # Check for invalid game states
        for game_id, game in self.games.items():
            if game.status not in ["pending", "completed", "failed"]:
                issues.append(f"Invalid status for game {game_id}: {game.status}")

            if game.retry_count < 0:
                issues.append(
                    f"Negative retry count for game {game_id}: {game.retry_count}"
                )

        return issues
