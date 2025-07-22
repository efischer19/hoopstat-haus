"""
State management for NBA season backfill application.

Implements checkpoint-based resumability with atomic updates
and comprehensive progress tracking.
"""

from datetime import datetime
from typing import Any

from hoopstat_observability import get_logger

logger = get_logger(__name__)


class BackfillState:
    """
    State management for backfill operation with checkpoint capability.

    Tracks progress, failed operations, and statistics to enable
    resumable backfill operations.
    """

    def __init__(self, backfill_id: str | None = None):
        """
        Initialize backfill state.

        Args:
            backfill_id: Unique identifier for this backfill run
        """
        self.backfill_id = backfill_id or self._generate_backfill_id()
        self.start_time = datetime.now().isoformat() + "Z"
        self.last_checkpoint = self.start_time

        # Progress tracking
        self.current_season: str | None = None
        self.completed_games: set[str] = set()
        self.failed_games: dict[str, dict[str, Any]] = {}
        self.skipped_games: set[str] = set()

        # Statistics
        self.statistics = {
            "total_games_processed": 0,
            "total_api_calls": 0,
            "total_bytes_stored": 0,
            "total_files_uploaded": 0,
            "processing_start_time": self.start_time,
            "last_checkpoint_time": self.start_time,
        }

        # Configuration tracking
        self.config_snapshot: dict[str, Any] = {}

        logger.info(
            "Backfill state initialized",
            backfill_id=self.backfill_id,
            start_time=self.start_time,
        )

    def _generate_backfill_id(self) -> str:
        """Generate unique backfill ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"nba-backfill-{timestamp}"

    def set_config_snapshot(self, config: dict[str, Any]) -> None:
        """
        Store configuration snapshot for resumability validation.

        Args:
            config: Configuration dictionary
        """
        self.config_snapshot = config.copy()

    def set_current_season(self, season: str) -> None:
        """
        Set the season being processed.

        Args:
            season: Season in format YYYY-YY
        """
        self.current_season = season
        logger.info(
            "Current season set",
            season=season,
            backfill_id=self.backfill_id,
        )

    def mark_game_completed(
        self,
        game_id: str,
        files_uploaded: int = 0,
        bytes_stored: int = 0,
        api_calls: int = 0,
    ) -> None:
        """
        Mark a game as successfully processed.

        Args:
            game_id: NBA game ID
            files_uploaded: Number of files uploaded for this game
            bytes_stored: Bytes stored for this game
            api_calls: Number of API calls made for this game
        """
        self.completed_games.add(game_id)

        # Remove from failed games if it was there
        self.failed_games.pop(game_id, None)

        # Update statistics
        self.statistics["total_games_processed"] += 1
        self.statistics["total_files_uploaded"] += files_uploaded
        self.statistics["total_bytes_stored"] += bytes_stored
        self.statistics["total_api_calls"] += api_calls

        logger.debug(
            "Game marked as completed",
            game_id=game_id,
            total_completed=len(self.completed_games),
            files_uploaded=files_uploaded,
            bytes_stored=bytes_stored,
        )

    def mark_game_failed(
        self,
        game_id: str,
        error_message: str,
        error_type: str,
        retry_count: int = 0,
    ) -> None:
        """
        Mark a game as failed with error details.

        Args:
            game_id: NBA game ID
            error_message: Error message
            error_type: Type of error
            retry_count: Number of retry attempts
        """
        self.failed_games[game_id] = {
            "error": error_message,
            "error_type": error_type,
            "retry_count": retry_count,
            "last_attempt": datetime.now().isoformat() + "Z",
        }

        logger.warning(
            "Game marked as failed",
            game_id=game_id,
            error_type=error_type,
            retry_count=retry_count,
            total_failed=len(self.failed_games),
        )

    def mark_game_skipped(self, game_id: str, reason: str) -> None:
        """
        Mark a game as skipped.

        Args:
            game_id: NBA game ID
            reason: Reason for skipping
        """
        self.skipped_games.add(game_id)

        logger.info(
            "Game marked as skipped",
            game_id=game_id,
            reason=reason,
            total_skipped=len(self.skipped_games),
        )

    def is_game_completed(self, game_id: str) -> bool:
        """Check if a game is already completed."""
        return game_id in self.completed_games

    def is_game_failed(self, game_id: str) -> bool:
        """Check if a game has failed."""
        return game_id in self.failed_games

    def get_failed_game_retry_count(self, game_id: str) -> int:
        """Get retry count for a failed game."""
        return self.failed_games.get(game_id, {}).get("retry_count", 0)

    def get_games_to_retry(self, max_retries: int) -> list[str]:
        """
        Get list of games that should be retried.

        Args:
            max_retries: Maximum retry attempts allowed

        Returns:
            List of game IDs to retry
        """
        return [
            game_id
            for game_id, failure in self.failed_games.items()
            if failure["retry_count"] < max_retries
        ]

    def update_checkpoint(self) -> None:
        """Update checkpoint timestamp."""
        self.last_checkpoint = datetime.now().isoformat() + "Z"
        self.statistics["last_checkpoint_time"] = self.last_checkpoint

        logger.debug(
            "Checkpoint updated",
            backfill_id=self.backfill_id,
            games_completed=len(self.completed_games),
            games_failed=len(self.failed_games),
        )

    def calculate_eta(
        self, total_games: int, processing_rate: float | None = None
    ) -> str | None:
        """
        Calculate estimated time to completion.

        Args:
            total_games: Total number of games to process
            processing_rate: Games per hour (calculated if not provided)

        Returns:
            ETA string or None if cannot calculate
        """
        if not processing_rate:
            # Calculate processing rate from current session
            start_time = datetime.fromisoformat(self.start_time.rstrip("Z"))
            elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600

            if elapsed_hours > 0 and len(self.completed_games) > 0:
                processing_rate = len(self.completed_games) / elapsed_hours
            else:
                return None

        remaining_games = total_games - len(self.completed_games)
        if processing_rate > 0:
            eta_hours = remaining_games / processing_rate
            eta_time = datetime.now().timestamp() + (eta_hours * 3600)
            return datetime.fromtimestamp(eta_time).isoformat()

        return None

    def get_progress_summary(self, total_games: int = 0) -> dict[str, Any]:
        """
        Get comprehensive progress summary.

        Args:
            total_games: Total number of games to process

        Returns:
            Progress summary dictionary
        """
        completed = len(self.completed_games)
        failed = len(self.failed_games)
        skipped = len(self.skipped_games)

        progress_pct = 0.0
        if total_games > 0:
            progress_pct = (completed / total_games) * 100

        eta = self.calculate_eta(total_games) if total_games > 0 else None

        return {
            "backfill_id": self.backfill_id,
            "current_season": self.current_season,
            "progress": {
                "completed_games": completed,
                "failed_games": failed,
                "skipped_games": skipped,
                "total_games": total_games,
                "progress_percentage": round(progress_pct, 2),
                "eta": eta,
            },
            "statistics": self.statistics.copy(),
            "timestamps": {
                "start_time": self.start_time,
                "last_checkpoint": self.last_checkpoint,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert state to dictionary for serialization.

        Returns:
            State data as dictionary
        """
        return {
            "backfill_id": self.backfill_id,
            "start_time": self.start_time,
            "last_checkpoint": self.last_checkpoint,
            "current_season": self.current_season,
            "completed_games": list(self.completed_games),
            "failed_games": self.failed_games,
            "skipped_games": list(self.skipped_games),
            "statistics": self.statistics,
            "config_snapshot": self.config_snapshot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackfillState":
        """
        Create state from dictionary (for resuming).

        Args:
            data: State data dictionary

        Returns:
            BackfillState instance
        """
        state = cls(data["backfill_id"])
        state.start_time = data["start_time"]
        state.last_checkpoint = data["last_checkpoint"]
        state.current_season = data.get("current_season")
        state.completed_games = set(data.get("completed_games", []))
        state.failed_games = data.get("failed_games", {})
        state.skipped_games = set(data.get("skipped_games", []))
        state.statistics = data.get("statistics", {})
        state.config_snapshot = data.get("config_snapshot", {})

        logger.info(
            "Backfill state loaded from checkpoint",
            backfill_id=state.backfill_id,
            completed_games=len(state.completed_games),
            failed_games=len(state.failed_games),
        )

        return state
